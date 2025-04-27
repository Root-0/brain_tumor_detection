# setup.py
from setuptools import setup, find_packages

setup(
    name="brain_tumor_detection",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'torch',
        'numpy',
        'SimpleITK',
        'nibabel',
        'pydicom'
    ],
)