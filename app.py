"""
Main application entry point for OCR Text Recognition
"""
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.controller import run_application


if __name__ == '__main__':
    # Change to script directory to ensure relative paths work
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the application
    exit_code = run_application()
    sys.exit(exit_code)
