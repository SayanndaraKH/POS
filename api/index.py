import os
import sys

# Add project root directory to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Expose app for Vercel WSGI handler
