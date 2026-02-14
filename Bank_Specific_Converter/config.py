#!/usr/bin/env python3
"""
Production Configuration for Bank Statement Converter
====================================================
Configuration settings for HestiaCP deployment
"""

import os
from pathlib import Path

class Config:
    # Security - SECRET_KEY MUST be set via environment variable
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY environment variable is required. Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")

    # Secure session settings
    SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Paths (adjust these based on your HestiaCP domain structure)
    BASE_DIR = Path(__file__).parent.absolute()
    UPLOAD_FOLDER = BASE_DIR / 'import'
    CONVERTED_FOLDER = BASE_DIR / 'export'
    DATA_DIR = BASE_DIR / 'data'

    # Bank converter scripts (should be in parent directory or same directory)
    SCRIPTS_DIR = BASE_DIR.parent

    # Database
    DATA_DIR.mkdir(exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DATA_DIR / "app.db"}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'timeout': 30},
        'pool_pre_ping': True,
    }

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