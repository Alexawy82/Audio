#!/usr/bin/env python3
"""
Setup script for DocToAudiobook web interface
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from setuptools import setup, find_packages

packages = [
    "flask",
    "python-docx",
    "PyPDF2",
    "pytesseract",
    "pdf2image",
    "pydub",
    "requests",
    "werkzeug",
    "ttkthemes"
]

def check_python_version():
    """Check if Python version is 3.8+"""
    print("Checking Python version...")
    if sys.version_info < (3, 8):
        print(f"Error: Python 3.8 or higher is required (You have {sys.version_info.major}.{sys.version_info.minor})")
        return False
    print(f"Python version {sys.version_info.major}.{sys.version_info.minor} is sufficient.")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("Packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        print("Please try installing manually:")
        print(f"  {sys.executable} -m pip install {' '.join(packages)}")
        return False
    except FileNotFoundError:
        print("Error: 'pip' command not found. Ensure Python and pip are installed and in your PATH.")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    print("Checking for Tesseract OCR...")
    try:
        import pytesseract
        # Attempt to get version to confirm it's working
        version = pytesseract.get_tesseract_version()
        print(f"Tesseract OCR found (version {version}).")
        return True
    except ImportError:
        print("Error: pytesseract library not found. Please ensure dependencies installed correctly.")
        return False # If pytesseract isn't installed, Tesseract check is irrelevant
    except pytesseract.TesseractNotFoundError:
        print("Warning: Tesseract OCR executable not found in PATH.")
    except Exception as e:
        # Catch other potential errors from get_tesseract_version
        print(f"Warning: Could not verify Tesseract OCR installation ({e}).")
        
    print("OCR functionality for PDF files may not work without Tesseract.")
    if sys.platform == 'win32':
        print("On Windows, download and install from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("Ensure you add the installation directory to your system's PATH.")
    elif sys.platform == 'darwin':
        print("On macOS, install with: brew install tesseract")
    else:
        print("On Linux, install using your package manager (e.g., sudo apt-get install tesseract-ocr)")
    return False # Return False as it wasn't definitively found and working

def create_directories():
    """Create necessary directories"""
    print("Creating necessary directories...")
    required_dirs = [
        "uploads",
        "templates",
        "static" # For potential future static web files
    ]
    try:
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Ensured directory exists: {dir_path.absolute()}")
        return True
    except Exception as e:
        print(f"Error creating directories: {e}")
        return False

def setup_config():
    """Create default configuration file if needed"""
    print("Setting up configuration file...")
    try:
        from config_manager import ConfigManager
        config_manager = ConfigManager() # This automatically creates default if not exists
        print(f"Configuration file checked/created at: {config_manager.config_path}")
        return True
    except ImportError as e:
        # This case is handled in main, but included for clarity
        raise # Re-raise the import error to be caught by main
    except Exception as e:
        print(f"Error during configuration setup: {e}")
        return False

def main():
    """Main setup function"""
    print("\n" + "=" * 60)
    print("DocToAudiobook Web Interface Setup - Starting...")
    print("=" * 60)
    
    try:
        if not check_python_version():
            return 1
        
        installed_ok = install_dependencies()
        if not installed_ok:
            print("\nDependency installation failed. Exiting setup.")
            return 1
        
        check_tesseract() # Continue even if Tesseract fails, but warn
        
        if not create_directories():
            print("\nFailed to create required directories. Exiting setup.")
            return 1
        
        try:
            if not setup_config():
                print("\nConfiguration setup step reported an issue. Exiting setup.")
                # Assuming setup_config returns False on failure, though it didn't originally
                return 1
        except ImportError as e:
            print(f"\nERROR: Failed to import ConfigManager: {e}")
            print("Please ensure 'config_manager.py' exists and has no errors.")
            return 1
        except Exception as e:
            print(f"\nERROR during config setup: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        print("\n" + "-" * 60)
        print("Setup completed successfully!")
        print("-" * 60)
        print("\nNext Steps:")
        print("1. If you haven't already, rename 'web_interface.py' to 'app.py'")
        print("2. Run the web interface: python app.py")
        print("3. Open your web browser to http://localhost:5000 (or the address shown)")
        print("4. Configure your OpenAI API key via the web interface.")
        print("\nNote: Ensure external tools like Tesseract/Poppler/FFmpeg are installed if needed.")
        print("=" * 60)
        
        return 0

    except Exception as e:
        print(f"\nAn unexpected error occurred during setup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

setup(
    name="doc2audiobook",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "openai",
        "python-docx",
        "pydub",
        "requests",
    ],
    python_requires=">=3.8",
) 