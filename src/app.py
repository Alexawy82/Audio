#!/usr/bin/env python3
"""
Web interface for DocToAudiobook tool
"""

# MONKEY PATCH: Fix OpenAI proxies issue
import os
import sys

# Force disable all proxy settings
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""
os.environ["http_proxy"] = ""
os.environ["https_proxy"] = ""
os.environ["OPENAI_PROXY"] = ""

# Patch the openai client if needed
def patch_openai():
    try:
        import importlib
        if 'openai' in sys.modules:
            # Reload the module to ensure our environment variables take effect
            importlib.reload(sys.modules['openai'])
            
        # Patch the OpenAI client initialization to ignore proxies
        try:
            from openai import OpenAI
            original_init = OpenAI.__init__
            
            def patched_init(self, *args, **kwargs):
                # Remove 'proxies' if present
                if 'proxies' in kwargs:
                    del kwargs['proxies']
                return original_init(self, *args, **kwargs)
                
            OpenAI.__init__ = patched_init
            print("OpenAI client successfully patched to ignore proxies")
        except (ImportError, AttributeError) as e:
            print(f"OpenAI patch not applied: {e}")
    except Exception as e:
        print(f"Error applying patch: {e}")

# Apply the patch
patch_openai()

import time
import uuid
import json
import threading
import zipfile
import io
import math
import logging
import argparse
from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify, session, flash, send_file
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from dotenv import load_dotenv
from datetime import datetime # Import datetime

# Load environment variables from .env file if present
load_dotenv()

# Set up data directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
UPLOAD_DIR = os.environ.get('UPLOAD_DIR', os.path.join(DATA_DIR, 'uploads'))
OUTPUT_DIR = os.environ.get('OUTPUT_FOLDER', os.path.join(DATA_DIR, 'output'))
TEMP_DIR = os.environ.get('TEMP_FOLDER', os.path.join(DATA_DIR, 'temp'))
CACHE_DIR = os.environ.get('CACHE_DIR', os.path.join(DATA_DIR, 'cache'))
DB_PATH = os.environ.get('DB_PATH', os.path.join(DATA_DIR, 'job_states.db'))

# Create necessary directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Import core modules individually to avoid circular imports
from core.config_manager import ConfigManager
from core.job_manager import job_manager
from core.utils.error import error_handler

# Import models
from core.models.tts import TTSSettings

# Import TTS components
from core.tts import enhanced
EnhancedTTS = enhanced.EnhancedTTS

# Import DocToAudiobook after other modules to avoid circular dependencies
from core.doc2audiobook import DocToAudiobook

# Configure logging
log_file = os.path.join(DATA_DIR, 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configure file upload settings
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['ALLOWED_EXTENSIONS'] = {'docx', 'pdf'}
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_UPLOAD_SIZE', 50 * 1024 * 1024))  # Default: 50MB
app.config['OUTPUT_FOLDER'] = OUTPUT_DIR
app.config['TEMP_FOLDER'] = TEMP_DIR
app.config['CACHE_DIR'] = CACHE_DIR
app.config['DB_PATH'] = DB_PATH

# Initialize config manager and get API key
config_manager = ConfigManager()
api_key = config_manager.get_api_key() or os.environ.get('OPENAI_API_KEY')
if api_key and not config_manager.get_api_key():
    config_manager.set_api_key(api_key)
    logger.info("API key loaded from environment variable")

# Preview handler is currently not available in our restructured code
# Initialize preview handler
# preview_handler = PreviewHandler(app, config_manager)

def get_converter():
    """Get a converter instance with current configuration."""
    global api_key
    # Update API key from config
    api_key = config_manager.get_api_key()
    if not api_key:
        raise ValueError("API key not configured")
    return DocToAudiobook(config_manager)

# Initialize converter with the API key from config
try:
    converter = get_converter()
except ValueError as e:
    logger.warning(f"Failed to initialize converter: {str(e)}")
    converter = None

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render main page."""
    # Use the global converter instance, which should have the latest key
    current_converter = converter 
    
    # Default values for voices, models and style presets
    voices = [
        {"id": "alloy", "name": "Alloy (Balanced)"},
        {"id": "echo", "name": "Echo (Soft)"},
        {"id": "fable", "name": "Fable (Narrative)"},
        {"id": "onyx", "name": "Onyx (Deep)"},
        {"id": "nova", "name": "Nova (Friendly)"},
        {"id": "shimmer", "name": "Shimmer (Clear)"}
    ]
    
    models = [
        {"id": "tts-1", "name": "TTS-1 (Standard)"},
        {"id": "tts-1-hd", "name": "TTS-1-HD (High Quality)"}
    ]
    
    style_presets = [
        {"id": "neutral", "name": "Neutral"},
        {"id": "cheerful", "name": "Cheerful"},
        {"id": "serious", "name": "Serious"},
        {"id": "excited", "name": "Excited"},
        {"id": "sad", "name": "Sad"},
        {"id": "custom", "name": "Custom Style"}
    ]
    
    # Default settings
    voice_settings = {
        "voice_id": "alloy",
        "model": "tts-1",
        "speed": 1.0,
        "style": "neutral",
        "emotion": ""
    }
    
    output_settings = {
        "format": "mp3",
        "bitrate": "192k",
        "normalize": True
    }
    
    # Only override defaults if converter is initialized
    if current_converter is not None:
        # Get available voices and models
        try:
            converter_voices = current_converter.get_available_voices()
            if converter_voices and len(converter_voices) > 0:
                voices = [{"id": v, "name": v.capitalize()} for v in converter_voices]
                
            converter_models = current_converter.get_available_models()
            if converter_models and len(converter_models) > 0:
                models = [{"id": m, "name": m} for m in converter_models]
                
            converter_style_presets = current_converter.get_voice_style_presets()
            if converter_style_presets and len(converter_style_presets) > 0:
                style_presets = [{"id": k, "name": k.capitalize()} for k in converter_style_presets.keys()]
                if not any(preset["id"] == "custom" for preset in style_presets):
                    style_presets.append({"id": "custom", "name": "Custom Style"})
                
            # Get current settings
            voice_settings = current_converter.voice_settings
            output_settings = current_converter.output_settings
        except Exception as e:
            logger.warning(f"Error getting converter settings: {e}")
            # Fall back to defaults
    
    # Get recent files
    recent_files = config_manager.get_recent_files()
    
    # Check if API key is configured using the global key variable
    api_configured = bool(api_key)
    
    return render_template(
        'index.html',
        voices=voices,
        models=models,
        style_presets=style_presets,
        voice_settings=voice_settings,
        output_settings=output_settings,
        recent_files=recent_files,
        api_configured=api_configured
    )

@app.route('/api/config', methods=['GET', 'POST'])
@error_handler.api_error_handler
def api_config():
    """Handle API configuration."""
    if request.method == 'POST':
        try:
            # Get form data - only API key
            api_key = request.form.get('api_key', '').strip()
            
            # Update API key if provided
            if api_key:
                # First validate the API key before saving
                try:
                    # Import our helper to get a clean OpenAI client
                    from core.utils.openai_helper import get_openai_client
                    
                    # Import our helper to get a clean OpenAI client
                    from core.utils.openai_helper import get_openai_client
                    
                    try:
                        # Create a clean client using our helper
                        client = get_openai_client(api_key)
                        
                        # Test the TTS API with a minimal request
                        response = client.audio.speech.create(
                            model="tts-1",
                            voice="alloy",
                            input="This is a test of the OpenAI API key.",
                            response_format="mp3"
                        )
                    except Exception as e:
                        logger.error(f"OpenAI client verification failed: {e}")
                        raise ValueError(f"Failed to validate OpenAI API key: {str(e)}")
                    
                    # If we get here, the API key is valid
                    # Now save it to the config
                    config_manager.set_api_key(api_key)
                    logger.info("API key validated and saved successfully")
                    
                    return jsonify({
                        'status': 'success',
                        'message': 'API key validated and saved successfully'
                    })
                    
                except ValueError as e:
                    # Handle specific validation errors
                    logger.error(f"API key validation failed: {e}")
                    return jsonify({
                        'status': 'error',
                        'message': str(e)
                    }), 400
                except Exception as e:
                    # Handle other unexpected errors
                    logger.error(f"Unexpected error during API key validation: {e}")
                    return jsonify({
                        'status': 'error',
                        'message': f'Error validating API key: {str(e)}'
                    }), 500
            
            return jsonify({
                'status': 'success',
                'message': 'API key updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating API key: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error updating API key: {str(e)}'
            }), 500
            
    # GET request - return current configuration
    return render_template('api_config.html',
                         api_key=config_manager.get_api_key())

@app.route('/api/clear-cache', methods=['POST'])
@error_handler.api_error_handler
def clear_tts_cache():
    """Clear the TTS cache to force regeneration of audio."""
    try:
        from core.tts.cache import TTSCache
        
        # Create cache instance
        cache = TTSCache(logger=logger)
        
        # Get stats before clearing
        before_stats = cache.get_cache_stats()
        logger.info(f"TTS cache stats before cleaning: {before_stats}")
        
        # Clear the cache
        result = cache.clear_cache(delete_files=True)
        
        logger.info(f"TTS cache cleared: {result}")
        
        return jsonify({
            'status': 'success',
            'entries_removed': result['entries_removed'],
            'files_deleted': result['files_deleted'],
            'space_freed_mb': result['space_freed_mb']
        })
    except Exception as e:
        logger.error(f"Error clearing TTS cache: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error clearing TTS cache: {str(e)}'
        }), 500

@app.route('/upload', methods=['POST'])
@error_handler.api_error_handler
def upload_file():
    """Handle file upload and start processing."""
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('index'))
        
    if not allowed_file(file.filename):
        flash('Invalid file type. Only DOCX and PDF files are allowed.', 'error')
        return redirect(url_for('index'))
        
    try:
        # Create job directory
        job_id = str(uuid.uuid4())
        job_dir = os.path.join(app.config['UPLOAD_FOLDER'], job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(job_dir, filename)
        
        # Ensure the file is saved successfully
        file.save(file_path)
        if not os.path.exists(file_path):
            raise Exception("Failed to save uploaded file")
            
        logger.info(f"File saved successfully at: {file_path}")
        
        # Get voice and output settings from form
        voice_settings = {
            'voice_id': request.form.get('voice_id', 'alloy'),
            'model': request.form.get('model', 'tts-1-hd'),
            'speed': float(request.form.get('speed', 1.0)),
            'style': request.form.get('style', 'neutral')
        }
        
        output_settings = {
            'format': request.form.get('format', 'mp3'),
            'bitrate': request.form.get('bitrate', '192k'),
            'normalize': request.form.get('normalize', 'true').lower() == 'true'
        }
        
        # Create job info
        job_info = {
            'id': job_id,
            'filename': filename,
            'file_path': file_path,
            'output_dir': job_dir,
            'voice_settings': voice_settings,
            'output_settings': output_settings,
            'status': 'queued',
            'created_at': time.time()
        }
        
        # Save job info
        job_json_path = os.path.join(job_dir, 'job.json')
        with open(job_json_path, 'w') as f:
            json.dump(job_info, f, indent=4)
            
        logger.info(f"Job info saved at: {job_json_path}")
        
        # Register job with job manager
        config = {
            'voice_settings': voice_settings,
            'output_settings': output_settings
        }
        job_manager.create_job(file_path, job_dir, config)
        job_manager.active_jobs[job_id] = job_info
            
        # Start processing in background
        thread = threading.Thread(target=process_job_thread, args=(job_id, file_path, job_dir))
        thread.daemon = True
        thread.start()
        
        flash('File uploaded successfully. Processing started.', 'success')
        return redirect(url_for('job_status', job_id=job_id))
        
    except Exception as e:
        logger.error(f"Error during file upload: {str(e)}", exc_info=True)
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/job/<job_id>')
@error_handler.api_error_handler
def job_status(job_id):
    """Show job status page."""
    try:
        # Get job data
        job = job_manager.get_job(job_id)
        if not job:
            flash('Job not found', 'error')
            return redirect(url_for('index'))
        
        # Add formatted values for display
        if job.get('status') == 'completed' and 'result' in job and 'output_files' in job['result']:
            for file in job['result']['output_files']:
                # Add formatted size and duration if not already present
                if 'size_formatted' not in file:
                    file['size_formatted'] = format_file_size(file.get('size', 0))
                if 'duration_formatted' not in file:
                    file['duration_formatted'] = format_duration(file.get('duration', 0))
                
                # Make sure we have a valid name
                if 'name' not in file and 'path' in file:
                    file['name'] = os.path.basename(file['path'])
                
        # Render the template with enhanced job data
        return render_template('job_status.html', job=job)
    except Exception as e:
        logger.error(f"Error displaying job status for {job_id}: {e}", exc_info=True)
        flash('Error displaying job status', 'error')
        return redirect(url_for('index'))

@app.route('/job/<job_id>/status')
@error_handler.api_error_handler
def job_status_api(job_id):
    """API endpoint for getting job status."""
    try:
        job = job_manager.get_job(job_id)
        if not job:
            return jsonify({'status': 'error', 'message': 'Job not found'}), 404
            
        return jsonify({
            'status': job['status'],
            'progress': job.get('progress', 0),
            'current_step': job.get('current_step', ''),
            'error': job.get('error', '')
        })
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def process_job_thread(job_id, input_file, output_dir):
    """Process a job in a separate thread."""
    try:
        # Get job information
        job = job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
            
        # Get filename from job
        filename = job.get('filename', os.path.basename(input_file))
        
        # Update job status to processing
        job_manager.update_job_status(job_id, "processing")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get or initialize converter
        try:
            converter = get_converter()
        except ValueError as e:
            job_manager.update_job_status(job_id, "failed", error=str(e))
            logger.error(f"Failed to initialize converter: {e}")
            return
            
        # Get settings from config
        voice_settings = config_manager.get_voice_settings()
        
        # Process document to audiobook
        try:
            # Update job step
            job_manager.update_job_progress(job_id, 10, "Converting document to text")
            
            # Convert document to audiobook
            result = converter.create_audiobook(
                input_file=input_file,
                output_dir=output_dir,
                style_map=voice_settings,
                max_chapters=30
            )
            
            # The result is now always a dictionary
            result_dict = result
            status = result_dict.get('status', 'unknown')
            output_files = result_dict.get('output_files', [])
            error_message = result_dict.get('error', None)
            metadata = result_dict.get('metadata', {})
                
            # Update job status based on conversion result
            if status == "completed":
                job_manager.update_job_status(job_id, "completed", result=result_dict)
                logger.info(f"Job {job_id} completed successfully")
            elif status == "partial":
                # Partial success - some chapters were processed
                total_chapters = metadata.get('total_chapters', 0)
                successful_chapters = metadata.get('successful_chapters', 0)
                
                # Consider it completed if at least one chapter was processed
                if output_files and successful_chapters > 0:
                    job_manager.update_job_status(job_id, "completed", result=result_dict)
                    logger.warning(f"Job {job_id} partially completed: {successful_chapters}/{total_chapters} chapters")
                else:
                    job_manager.update_job_status(job_id, "failed", 
                                             error=f"Partial conversion with no usable output: {successful_chapters}/{total_chapters} chapters")
                    logger.error(f"Job {job_id} failed with partial conversion: {successful_chapters}/{total_chapters} chapters")
            else:
                job_manager.update_job_status(job_id, "failed", 
                                           error=error_message or f"Conversion failed with status: {status}")
                logger.error(f"Job {job_id} failed: {status} - {error_message or 'No error details'}")
                
        except Exception as e:
            # Update job status to failed
            job_manager.update_job_status(job_id, "failed", error=str(e))
            logger.error(f"Error processing job {job_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error in job thread for {job_id}: {e}")
        job_manager.update_job_status(job_id, "failed", error=str(e))

@app.route('/download/<job_id>/<filename>')
@error_handler.api_error_handler
def download_file(job_id, filename):
    """Download a single output file."""
    try:
        logger.info(f"Download request for job {job_id}, file {filename}")
        
        # Get job from job manager
        job = job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return jsonify({'error': 'Job not found'}), 404

        # Validate output directory
        output_dir = job.get('output_dir')
        if not output_dir or not isinstance(output_dir, str) or not os.path.isdir(output_dir):
            logger.error(f"Invalid output directory '{output_dir}' for job {job_id}")
            return "Output directory not found or invalid for this job.", 404

        # Find the target file
        target_file_path = None
        output_files = job.get('result', {}).get('output_files', [])
        
        logger.info(f"Job {job_id} has {len(output_files)} output files")
        
        # First try to find by exact filename match
        for file_details in output_files:
            stored_filename = file_details.get('name')
            stored_filepath = file_details.get('path')
            
            # Log the file details we're checking
            logger.debug(f"Checking file: {stored_filename} at path: {stored_filepath}")

            # Validate file details
            if not stored_filename or not isinstance(stored_filename, str):
                logger.warning(f"Invalid filename in job {job_id} details: {file_details}")
                continue
            if not stored_filepath or not isinstance(stored_filepath, str):
                logger.warning(f"Invalid file path for '{stored_filename}' in job {job_id}")
                continue

            # Compare filenames with normalized security
            if secure_filename(stored_filename) == secure_filename(filename):
                logger.info(f"Found matching filename: {stored_filename}")
                
                # Check if the file exists at the stored path
                if os.path.exists(stored_filepath):
                    logger.info(f"File exists at path: {stored_filepath}")
                    target_file_path = stored_filepath
                    break
                else:
                    # Try to find the file in the output directory with the same name
                    alt_path = os.path.join(output_dir, stored_filename)
                    if os.path.exists(alt_path):
                        logger.info(f"File found at alternative path: {alt_path}")
                        target_file_path = alt_path
                        break
                    else:
                        logger.warning(f"File not found at path: {stored_filepath} or {alt_path}")
        
        # If we didn't find by exact name, try to find by looking in the output directory
        if not target_file_path:
            logger.info(f"Exact match not found, searching in output directory: {output_dir}")
            # Look for the file in output_dir
            potential_path = os.path.join(output_dir, secure_filename(filename))
            if os.path.exists(potential_path):
                logger.info(f"Found file directly in output directory: {potential_path}")
                target_file_path = potential_path
            else:
                # Search all files in directory to find a match by name
                for file in os.listdir(output_dir):
                    if secure_filename(file) == secure_filename(filename):
                        potential_path = os.path.join(output_dir, file)
                        if os.path.isfile(potential_path):
                            logger.info(f"Found file by directory scan: {potential_path}")
                            target_file_path = potential_path
                            break

        # Return file if found
        if target_file_path:
            logger.info(f"Sending file: {target_file_path}")
            # Make sure we have mime_type for audio files
            _, ext = os.path.splitext(target_file_path)
            mime_type = None
            
            # Check if this is a streaming request (from audio player) or download request
            # If the request includes "Range" header, it's likely a streaming request from an audio player
            # or if the "play" parameter is in the request args
            is_streaming = "Range" in request.headers or request.args.get('play') == '1'
            as_attachment = not is_streaming
            
            # Log request info
            logger.info(f"Request headers: {request.headers.get('Range', 'No Range header')}")
            logger.info(f"Streaming request: {is_streaming}, as_attachment: {as_attachment}")
            
            # Set appropriate mime type for common audio files
            if ext.lower() == '.mp3':
                mime_type = 'audio/mpeg'
            elif ext.lower() == '.wav':
                mime_type = 'audio/wav'
            elif ext.lower() == '.ogg':
                mime_type = 'audio/ogg'
            
            # Send file with correct mime type
            return send_file(
                target_file_path, 
                mimetype=mime_type,
                as_attachment=as_attachment,
                download_name=secure_filename(filename)
            )
        else:
            logger.error(f"File '{filename}' not found for job {job_id}")
            return "File not found or invalid", 404

    except FileNotFoundError as e:
        logger.error(f"File not found for job {job_id}: {e}")
        return "File not found", 404
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding job data for job {job_id}: {e}")
        return "Error reading job data", 500
    except Exception as e:
        logger.error(f"Error during file download for job {job_id}: {e}", exc_info=True)
        return "Error processing download request", 500

@app.route('/download-all/<job_id>')
def download_all(job_id):
    """Download all output files as a zip archive."""
    try:
        logger.info(f"Download all request for job {job_id}")
        
        job = job_manager.get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found for download-all")
            return "Job not found", 404
        
        output_dir = job.get('output_dir') # Get the output dir path
        audio_files_info = job.get('result', {}).get('output_files', [])
        
        logger.info(f"Job {job_id} has {len(audio_files_info)} output files in info")
        
        # Check if there are files to download and the output dir exists
        if not output_dir or not os.path.isdir(output_dir):
            logger.error(f"Output directory missing for job {job_id}: {output_dir}")
            flash('Output directory missing for this job.', 'error')
            return redirect(url_for('job_status', job_id=job_id) or url_for('index'))
        
        # Create a zip file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            added_files = 0
            
            # First try to add files from the job info
            if audio_files_info:
                logger.info(f"Attempting to add {len(audio_files_info)} files from job info")
                for file_details in audio_files_info:
                    file_path_from_job = file_details.get('path')
                    filename_in_zip = secure_filename(file_details.get('name', f'file_{added_files}.mp3'))
                    
                    # Check if the file path exists and is within the output directory
                    if file_path_from_job and os.path.exists(file_path_from_job) and \
                       os.path.abspath(file_path_from_job).startswith(os.path.abspath(output_dir)):
                        # Add file to zip using the clean filename
                        zf.write(file_path_from_job, filename_in_zip)
                        added_files += 1
                        logger.info(f"Added file to zip: {file_path_from_job} as {filename_in_zip}")
                    else:
                        logger.warning(f"File from job info not found: {file_path_from_job}")
                        # Try to find the file in the output directory
                        alt_path = os.path.join(output_dir, filename_in_zip)
                        if os.path.exists(alt_path):
                            zf.write(alt_path, filename_in_zip)
                            added_files += 1
                            logger.info(f"Added file to zip from alternative path: {alt_path}")
            
            # If no files were added from job info, try to add all MP3 files from the output directory
            if added_files == 0:
                logger.info(f"No files added from job info, scanning output directory: {output_dir}")
                # Find all audio files in the output directory
                for file in os.listdir(output_dir):
                    file_path = os.path.join(output_dir, file)
                    # Only include MP3 files
                    if os.path.isfile(file_path) and file.lower().endswith('.mp3'):
                        safe_filename = secure_filename(file)
                        zf.write(file_path, safe_filename)
                        added_files += 1
                        logger.info(f"Added file to zip from directory scan: {file_path}")

        # Check if any files were actually added
        if added_files == 0:
            logger.error(f"No files found to include in zip for job {job_id}")
            flash('Could not find any valid audio files to include in the zip archive.', 'error')
            return redirect(url_for('job_status', job_id=job_id) or url_for('index'))

        # Seek to the beginning of the stream
        memory_file.seek(0)
        
        # Generate a nice zip filename based on the original document
        document_title_stem = Path(secure_filename(job.get('filename', 'document'))).stem
        zip_filename = f"{document_title_stem}_audiobook.zip"
        
        logger.info(f"Sending zip with {added_files} files for job {job_id}")
        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        logger.error(f"Error creating zip archive for job {job_id}: {e}", exc_info=True)
        flash('Error creating zip archive', 'error')
        return redirect(url_for('index'))

# --- Helper Functions for Formatting --- START ---
def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes is None:
        return "Unknown"
    
    try:
        size_bytes = float(size_bytes)
    except (ValueError, TypeError):
        return "Invalid size"
        
    if size_bytes < 1024:
        return f"{size_bytes:.0f} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes/(1024*1024):.1f} MB"
    return f"{size_bytes/(1024*1024*1024):.2f} GB"

def format_duration(seconds):
    """Format duration in human-readable format."""
    # Handle potential None or negative values
    if seconds is None or seconds < 0:
        return "0:00"
        
    try:
        seconds = float(seconds)
    except (ValueError, TypeError):
        return "Unknown"
        
    if seconds < 60:
        # For very short durations, show seconds with one decimal place
        return f"{seconds:.1f} sec"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        sec = int(seconds % 60)
        return f"{minutes}:{sec:02d}"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        sec = int(seconds % 60)
        return f"{hours}:{minutes:02d}:{sec:02d}"
# --- Helper Functions for Formatting --- END ---

# ----- Preview Handling ----- #
@app.route('/api/preview', methods=['POST'])
@error_handler.api_error_handler
def generate_preview():
    """Generate a preview audio clip."""
    try:
        # Get text and voice settings from request
        text = request.form.get('text', '')
        model = request.form.get('model', 'tts-1')
        voice_id = request.form.get('voice_id', 'alloy')
        speed = float(request.form.get('speed', 1.0))
        style = request.form.get('style', 'neutral')
        emotion = request.form.get('emotion', '')
        
        if not text:
            return jsonify({
                'status': 'error',
                'message': 'Please provide text to preview'
            }), 400
            
        # Check if we have a valid API key
        api_key = config_manager.get_api_key()
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'API key not configured'
            }), 400
            
        # Create temporary file for preview
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            temp_path = tmp.name
            
        # Generate audio
        try:
            # Import our helper to get a clean OpenAI client
            from core.utils.openai_helper import get_openai_client
            
            try:
                # Create a clean client using our helper
                client = get_openai_client(api_key)
                
                # Call the TTS API
                response = client.audio.speech.create(
                    model=model,
                    voice=voice_id,
                    input=text[:1000],  # Limit preview text to 1000 chars
                    response_format="mp3"
                )
            except Exception as e:
                logger.error(f"Error with OpenAI API call: {e}")
                return jsonify({
                    'status': 'error',
                    'message': f'Error with OpenAI API: {str(e)}'
                }), 500
            
            # Save the audio to a temporary file
            with open(temp_path, 'wb') as f:
                response_bytes = response.content
                f.write(response_bytes)
                
            # Return the audio file
            return send_file(
                temp_path,
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name='preview.mp3'
            )
            
        except Exception as e:
            logger.error(f"Error generating preview: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Error generating preview: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in preview handler: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

# ---------------- Jinja Custom Filter ------------------

def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    """Format a datetime object for display."""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            # Attempt to parse if it's an ISO string (common format)
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value # Return original string if parsing fails
    if not isinstance(value, datetime):
        return value # Return as is if not a datetime object
    return value.strftime(format)

# Register custom filters and tests with Jinja
app.jinja_env.filters['datetime'] = format_datetime

# Add custom test for string containing
def containing_test(value, other):
    return other in value if value is not None else False

app.jinja_env.tests['containing'] = containing_test

# Health check endpoint for monitoring
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connectivity and job manager
        job_count = len(job_manager.get_all_jobs())
        
        # Check if we can initialize the converter (API key check)
        api_key_set = config_manager.get_api_key() is not None
        
        # Check if required directories exist
        data_dirs_exist = all(os.path.exists(path) for path in [
            UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR, CACHE_DIR
        ])
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'jobs': job_count,
            'api_key_configured': api_key_set,
            'data_directories': data_dirs_exist,
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='DocToAudiobook Web Interface')
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 5000)), 
                        help='Port to run the application on')
    parser.add_argument('--host', type=str, default=os.environ.get('HOST', '0.0.0.0'), 
                        help='Host to run the application on')
    parser.add_argument('--debug', action='store_true', default=os.environ.get('DEBUG', 'false').lower() == 'true',
                        help='Run in debug mode')
    args = parser.parse_args()
    
    # Check for required dependencies
    try:
        from pydub.utils import which
        if not which("ffmpeg"):
            logger.warning("FFmpeg not found. Audio processing functionality may not work properly.")
            logger.warning("Please install FFmpeg: https://ffmpeg.org/download.html")
    except Exception as e:
        logger.warning(f"Error checking for FFmpeg: {e}")
    
    logger.info(f"Starting DocToAudiobook on {args.host}:{args.port}")
    
    # Run the application
    app.run(debug=args.debug, host=args.host, port=args.port) 