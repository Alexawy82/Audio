#!/usr/bin/env python3
"""
DocToAudiobook Runner Script
Provides a simple interface to start and manage the application
"""

import os
import sys
import argparse
import subprocess
import time
import shutil
import webbrowser

# Add the src directory to the path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        # Check for Python packages
        import flask
        import pydub
        import openai
        
        # Check for ffmpeg
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            print("⚠️ WARNING: FFmpeg not found. Audio processing will not work.")
            return False
            
        return True
    except ImportError as e:
        print(f"⚠️ Missing dependencies: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def run_diagnostics():
    """Run diagnostics to check system setup."""
    script_path = os.path.join(BASE_DIR, "src", "diagnose.py")
    cmd = [sys.executable, script_path, "--all"]
    
    print("🔍 Running diagnostics...")
    subprocess.run(cmd)

def run_cleanup():
    """Run cleanup script to remove temporary files."""
    script_path = os.path.join(BASE_DIR, "src", "cleanup.py")
    cmd = [sys.executable, script_path, "--all"]
    
    print("🧹 Running cleanup...")
    subprocess.run(cmd)

def run_app(port=5000, debug=False, open_browser=True):
    """Run the main application."""
    if not check_dependencies():
        print("Would you like to run anyway? (y/n)")
        response = input("> ")
        if response.lower() != "y":
            return
    
    app_path = os.path.join(BASE_DIR, "src", "app.py")
    cmd = [sys.executable, app_path, "--port", str(port)]
    
    if debug:
        cmd.append("--debug")
    
    print(f"🚀 Starting DocToAudiobook on port {port}...")
    
    if open_browser:
        # Open browser after a short delay
        def open_app_in_browser():
            time.sleep(2)
            webbrowser.open(f"http://localhost:{port}")
        
        import threading
        browser_thread = threading.Thread(target=open_app_in_browser)
        browser_thread.daemon = True
        browser_thread.start()
    
    try:
        # Run in foreground, pass through Ctrl+C
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n👋 DocToAudiobook stopped")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DocToAudiobook Runner")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the application on")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--diag", action="store_true", help="Run diagnostics only")
    parser.add_argument("--clean", action="store_true", help="Run cleanup only")
    
    args = parser.parse_args()
    
    # Create data directories if they don't exist
    os.makedirs(os.path.join(BASE_DIR, "data", "uploads"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data", "output"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data", "temp"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data", "cache"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "data", "logs"), exist_ok=True)
    
    if args.diag:
        run_diagnostics()
    elif args.clean:
        run_cleanup()
    else:
        run_app(
            port=args.port, 
            debug=args.debug, 
            open_browser=not args.no_browser
        )