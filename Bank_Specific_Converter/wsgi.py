#!/usr/bin/env python3
"""
WSGI Configuration for Bank Statement Converter
===============================================
Production WSGI entry point for HestiaCP deployment
"""

import sys
import os

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app import app

# WSGI application entry point
application = app

if __name__ == "__main__":
    app.run()