# brain_tumor_detection/api/main.py

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import uuid
import shutil
import logging
import datetime
import jwt
from jwt.exceptions import InvalidTokenError
import tempfile
import asyncio
from sqlalchemy.orm import Session

from brain_tumor_detection.Backend.api.inference_service import BrainTumorInferenceService
from brain_tumor_detection.Backend.api.database import get_db, ScanRecord, User
from brain_tumor_detection.Backend.api.security import create_access_token, get_password_hash, verify_password, get_current_user
from brain_tumor_detection.Backend.api.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Brain Tumor Detection API",
    description="API for deep learning-based automated detection of brain tumors from MRI scans",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize inference service
inference_service = BrainTumorInferenceService(
    model_path=settings.MODEL_PATH,
    device=settings.DEVICE
)

# Define request/response models
class PredictionResponse(BaseModel):
    scan_id: str
    status: str
    result: Optional[Dict[str, Any]] = None

# Routes
@app.post("/api/auth/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/auth/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), 
                                db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/predict", response_model=PredictionResponse)
async def predict(background_tasks: BackgroundTasks,
                file: UploadFile = File(...),
                current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    """
    Upload an MRI scan for tumor detection
    """
    # Generate a unique ID for this scan
    scan_id = str(uuid.uuid4())
    
    # Create a temporary directory for this scan
    temp_dir = os.path.join(tempfile.gettempdir(), scan_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Save the uploaded file
        file_path = os.path.join(temp_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create record in database
        db_scan = ScanRecord(
            id=scan_id,
            user_id=current_user.id,
            filename=file.filename,
            status="processing"
        )
        db.add(db_scan)
        db.commit()
        
        # Process scan in the background
        background_tasks.add_task(
            process_scan_task, 
            scan_id=scan_id, 
            file_path=file_path,
            temp_dir=temp_dir
        )
        
        return {
            "scan_id": scan_id,
            "status": "processing",
            "result": None,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during file upload: {str(e)}"
        )

@app.get("/api/predict/{scan_id}", response_model=PredictionResponse)
async def get_prediction(scan_id: str, 
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    """
    Get the results of a scan by ID
    """
    # Get scan record from database
    scan = db.query(ScanRecord).filter(
        ScanRecord.id == scan_id,
        ScanRecord.user_id == current_user.id
    ).first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    return {
        "scan_id": scan.id,
        "status": scan.status,
        "result": scan.result if scan.result else None,
        "error": scan.error if scan.error else None
    }

@app.get("/api/users/scans", response_model=List[ScanHistoryItem])
async def get_user_scans(current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    """
    Get scan history for the current user
    """
    scans = db.query(ScanRecord).filter(
        ScanRecord.user_id == current_user.id
    ).order_by(ScanRecord.created_at.desc()).all()
    
    return [
        {
            "scan_id": scan.id,
            "filename": scan.filename,
            "status": scan.status,
            "created_at": scan.created_at,
            "result": scan.result
        }
        for scan in scans
    ]

@app.post("/api/batch", response_model=Dict[str, str])
async def batch_process(request: BatchRequest,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """
    Change status of multiple scans
    """
    # Check if user has access to all scans
    for scan_id in request.scan_ids:
        scan = db.query(ScanRecord).filter(
            ScanRecord.id == scan_id,
            ScanRecord.user_id == current_user.id
        ).first()
        
        if not scan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scan {scan_id} not found or access denied"
            )
    
    # Process the batch request
    # (In a real implementation, this would depend on what batch operation is needed)
    return {"status": "accepted", "message": f"Processing {len(request.scan_ids)} scans"}

@app.get("/api/model/info")
async def get_model_info():
    """
    Get information about the currently loaded model
    """
    return {
        "model_name": "UNet with ResNet50 Encoder",
        "version": "1.0.0",
        "last_updated": "2025-04-12",
        "accuracy": 0.94,
        "sensitivity": 0.92,
        "specificity": 0.96,
        "dice_coefficient": 0.89
    }

# Helper functions
async def process_scan_task(scan_id: str, file_path: str, temp_dir: str):
    """Background task to process an MRI scan"""
    db = next(get_db())
    
    try:
        # Get the scan record
        scan = db.query(ScanRecord).filter(ScanRecord.id == scan_id).first()
        if not scan:
            logger.error(f"Scan {scan_id} not found in database")
            return
        
        # Process the scan
        result = inference_service.process_scan(file_path)
        
        # Update the database record
        scan.status = "completed"
        scan.result = result
        scan.completed_at = datetime.datetime.now()
        db.commit()
        
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
    except Exception as e:
        logger.error(f"Error processing scan {scan_id}: {str(e)}")
        
        # Update database with error
        scan.status = "failed"
        scan.error = str(e)
        db.commit()
        
        # Clean up temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# Run app with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    error: Optional[str] = None
    
class BatchRequest(BaseModel):
    scan_ids: List[str]

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None

class ScanHistoryItem(BaseModel):
    scan_id: str
    filename: str
    status: str
    created_at: datetime.datetime
    result: Optional[Dict[str, Any]] = None