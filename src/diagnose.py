#!/usr/bin/env python3
"""
Diagnostic script for DocToAudiobook
Tests various components and checks system requirements
"""

import os
import sys
import logging
import platform
import shutil
import json
import importlib
import tempfile
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the src directory to the path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def check_python_version():
    """Check Python version."""
    python_version = sys.version_info
    logger.info(f"Python version: {platform.python_version()}")
    
    # Check if Python version is 3.9 or higher
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        logger.warning("Python version 3.9 or higher is recommended.")
        return False
    
    return True

def check_dependencies():
    """Check if all required dependencies are installed."""
    logger.info("Checking dependencies...")
    
    required_packages = [
        "flask",
        "pydub",
        "openai",
        "httpx", 
        "python-docx",
        "PyPDF2",
        "python-dotenv"
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            importlib.import_module(package)
            logger.info(f"{package}: Installed")
        except ImportError:
            logger.error(f"{package}: Not installed")
            all_installed = False
    
    return all_installed

def check_ffmpeg():
    """Check if FFmpeg is installed."""
    logger.info("Checking FFmpeg...")
    
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        logger.info(f"FFmpeg found at: {ffmpeg_path}")
        return True
    else:
        logger.error("FFmpeg not found. Audio processing will not work.")
        return False

def check_openai_api_key():
    """Check if OpenAI API key is configured."""
    logger.info("Checking OpenAI API key...")
    
    # Try to get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # Try to get API key from config
    try:
        from src.core.config_manager import ConfigManager
        config_manager = ConfigManager()
        config_api_key = config_manager.get_api_key()
        
        if config_api_key:
            logger.info("OpenAI API key found in config.")
            return True
    except Exception as e:
        logger.error(f"Error checking config for API key: {e}")
    
    if api_key:
        logger.info("OpenAI API key found in environment variables.")
        return True
    else:
        logger.warning("OpenAI API key not found. TTS functionality will not work.")
        return False

def check_file_permissions():
    """Check if the application has necessary file permissions."""
    logger.info("Checking file permissions...")
    
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # List of directories to check
    directories = [
        os.path.join(data_dir, "uploads"),
        os.path.join(data_dir, "output"),
        os.path.join(data_dir, "temp"),
        os.path.join(data_dir, "cache"),
        os.path.join(data_dir, "logs"),
        os.path.join(data_dir, "database")
    ]
    
    all_permissions_ok = True
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
        # Test write permission
        try:
            test_file = os.path.join(directory, ".test_write_permission")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            logger.info(f"{directory}: Write permission OK")
        except Exception as e:
            logger.error(f"{directory}: Write permission FAILED - {e}")
            all_permissions_ok = False
    
    return all_permissions_ok

def check_tts_functionality():
    """Test basic TTS functionality."""
    logger.info("Checking TTS functionality...")
    
    try:
        from src.core.tts.enhanced import EnhancedTTS
        from src.core.models.tts import TTSSettings
        
        # Create TTS engine
        tts = EnhancedTTS()
        
        # Test API key
        if tts.test_api_key():
            logger.info("OpenAI API key is valid.")
            
            # Test text generation
            try:
                settings = TTSSettings(
                    voice="alloy",
                    model="tts-1",
                    speed=1.0
                )
                
                # Generate a short test audio
                test_text = "This is a test of the text to speech system."
                audio = tts.generate_audio(test_text, settings)
                
                if audio and len(audio) > 0:
                    logger.info(f"Successfully generated test audio: {len(audio)/1000:.2f} seconds")
                    
                    # Save test audio to temp file
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                        test_file = tmp.name
                    
                    audio.export(test_file, format="mp3")
                    file_size = os.path.getsize(test_file)
                    
                    logger.info(f"Test file saved to {test_file} ({file_size} bytes)")
                    
                    # Clean up
                    os.remove(test_file)
                    
                    return True
                else:
                    logger.error("Generated audio is empty or invalid")
                    return False
                    
            except Exception as e:
                logger.error(f"Error generating test audio: {e}")
                return False
        else:
            logger.error("OpenAI API key validation failed.")
            return False
            
    except Exception as e:
        logger.error(f"Error testing TTS functionality: {e}")
        return False

def check_document_processing():
    """Test basic document processing functionality."""
    logger.info("Checking document processing functionality...")
    
    try:
        from src.core.document_processor import DocumentProcessor
        
        # Create document processor
        processor = DocumentProcessor()
        
        # Check docx support
        try:
            import docx
            logger.info("DOCX support: Available")
        except ImportError:
            logger.warning("DOCX support: Not available")
        
        # Check PDF support
        try:
            import PyPDF2
            logger.info("PDF support: Available")
        except ImportError:
            logger.warning("PDF support: Not available")
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking document processing: {e}")
        return False

def run_full_diagnosis():
    """Run all diagnostic checks."""
    logger.info("Running full system diagnosis...")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Platform: {platform.platform()}")
    
    # Run all checks
    checks = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        "FFmpeg": check_ffmpeg(),
        "OpenAI API Key": check_openai_api_key(),
        "File Permissions": check_file_permissions(),
        "Document Processing": check_document_processing()
    }
    
    # TTS test is optional
    if checks["OpenAI API Key"]:
        checks["TTS Functionality"] = check_tts_functionality()
    
    # Print summary
    logger.info("\n--- Diagnosis Summary ---")
    all_passed = True
    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"{name}: {status}")
        all_passed = all_passed and passed
    
    return all_passed

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DocToAudiobook Diagnostic Tool")
    parser.add_argument("--python", action="store_true", help="Check Python version")
    parser.add_argument("--deps", action="store_true", help="Check dependencies")
    parser.add_argument("--ffmpeg", action="store_true", help="Check FFmpeg")
    parser.add_argument("--api", action="store_true", help="Check OpenAI API key")
    parser.add_argument("--perms", action="store_true", help="Check file permissions")
    parser.add_argument("--tts", action="store_true", help="Test TTS functionality")
    parser.add_argument("--docs", action="store_true", help="Test document processing")
    parser.add_argument("--all", action="store_true", help="Run all checks")
    
    args = parser.parse_args()
    
    # If no arguments provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)
    
    # Run selected checks
    if args.all:
        success = run_full_diagnosis()
    else:
        success = True
        
        if args.python:
            success = check_python_version() and success
        
        if args.deps:
            success = check_dependencies() and success
        
        if args.ffmpeg:
            success = check_ffmpeg() and success
        
        if args.api:
            success = check_openai_api_key() and success
        
        if args.perms:
            success = check_file_permissions() and success
        
        if args.tts:
            success = check_tts_functionality() and success
        
        if args.docs:
            success = check_document_processing() and success
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)