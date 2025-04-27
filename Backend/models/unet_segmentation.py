# brain_tumor_detection/models/unet_segmentation.py

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models

class EncoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(EncoderBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=2, stride=2)
        
    def forward(self, x):
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        skip_connection = x
        x = self.maxpool(x)
        return x, skip_connection

class DecoderBlock(nn.Module):
    def __init__(self, in_channels, out_channels, use_attention=True):
        super(DecoderBlock, self).__init__()
        self.upconv = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.attention = AttentionBlock(out_channels, out_channels) if use_attention else None

    def forward(self, x, skip_connection):
        x = self.upconv(x)
        
        # Ensure the dimensions match for the concatenation
        diffY = skip_connection.size()[2] - x.size()[2]
        diffX = skip_connection.size()[3] - x.size()[3]
        
        x = F.pad(x, [diffX // 2, diffX - diffX // 2, diffY // 2, diffY - diffY // 2])
        # Apply attention to skip connection if enabled
        if self.attention is not None:
            skip_connection = self.attention(x, skip_connection)
        x = torch.cat([x, skip_connection], dim=1)
        
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.relu(self.bn2(self.conv2(x)))
        return x

    def __init__(self, in_channels, out_channels, use_attention=True):
        super().__init__()
        self.attention = AttentionBlock(out_channels, out_channels) if use_attention else None

class UNetModel(nn.Module):
    def __init__(self, num_classes=1, pretrained=True):
        super(UNetModel, self).__init__()
        
        # Load pretrained ResNet50 as encoder backbone
        backbone = models.resnet50(pretrained=pretrained)
        
        # Extract encoder layers from ResNet
        self.firstconv = backbone.conv1
        self.firstbn = backbone.bn1
        self.firstrelu = backbone.relu
        self.firstmaxpool = backbone.maxpool
        self.encoder1 = backbone.layer1
        self.encoder2 = backbone.layer2
        self.encoder3 = backbone.layer3
        self.encoder4 = backbone.layer4
        
        # Define decoder layers
        self.decoder4 = DecoderBlock(2048, 1024)
        self.decoder3 = DecoderBlock(1024, 512)
        self.decoder2 = DecoderBlock(512, 256)
        self.decoder1 = DecoderBlock(256, 64)
        
        # Final layer for segmentation
        self.final_conv = nn.Conv2d(64, num_classes, kernel_size=1)
        
    def forward(self, x):
        # Encoder path
        x = self.firstconv(x)
        x = self.firstbn(x)
        x = self.firstrelu(x)
        skip1 = x
        x = self.firstmaxpool(x)
        
        x = self.encoder1(x)
        skip2 = x
        
        x = self.encoder2(x)
        skip3 = x
        
        x = self.encoder3(x)
        skip4 = x
        
        x = self.encoder4(x)
        
        # Decoder path
        x = self.decoder4(x, skip4)
        x = self.decoder3(x, skip3)
        x = self.decoder2(x, skip2)
        x = self.decoder1(x, skip1)
        
        # Final segmentation layer
        x = self.final_conv(x)
        return x

class AttentionBlock(nn.Module):
    def __init__(self, F_g, F_l):
        super().__init__()
        self.W_g = nn.Sequential(
            nn.Conv2d(F_g, F_l, kernel_size=1),
            nn.BatchNorm2d(F_l)
        )
        self.psi = nn.Sequential(
            nn.Conv2d(F_l, 1, kernel_size=1),
            nn.BatchNorm2d(1),
            nn.Sigmoid()
        )

    def forward(self, g, x):
        g1 = self.W_g(g)
        x1 = x
        psi = F.relu(g1 + x1)
        psi = self.psi(psi)
        return x * psi

