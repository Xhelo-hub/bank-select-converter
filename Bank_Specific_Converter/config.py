#!/usr/bin/env python3
"""
Production Configuration for Bank Statement Converter
====================================================
Configuration settings for HestiaCP deployment
"""

import os
from pathlib import Path

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bank-specific-converter-production-key-change-this'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Paths (adjust these based on your HestiaCP domain structure)
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = BASE_DIR / 'import'
    CONVERTED_FOLDER = BASE_DIR / 'export'
    
    # Bank converter scripts (should be in parent directory or same directory)
    SCRIPTS_DIR = BASE_DIR.parent
    
    # Production settings
    DEBUG = False
    TESTING = False
    
    # Ensure directories exist
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    CONVERTED_FOLDER.mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    
# Default configuration
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}