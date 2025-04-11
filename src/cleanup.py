#!/usr/bin/env python3
"""
Cleanup script for DocToAudiobook.
Handles removal of temporary files, cache cleanup, and directory organization.
"""

import os
import shutil
import argparse
import logging
import json
from pathlib import Path
from typing import List, Set
import time

# Add the src directory to the path
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.core.config_manager import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def clean_pycache(base_dir: str = BASE_DIR) -> int:
    """
    Remove all __pycache__ directories.
    
    Args:
        base_dir: The base directory to start the search
        
    Returns:
        Number of directories removed
    """
    logger.info("Cleaning __pycache__ directories...")
    count = 0
    for root, dirs, _ in os.walk(base_dir):
        if '__pycache__' in dirs:
            pycache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_dir)
                logger.info(f"Removed: {pycache_dir}")
                count += 1
            except Exception as e:
                logger.error(f"Error removing {pycache_dir}: {e}")
    
    logger.info(f"Removed {count} __pycache__ directories")
    return count

def clean_empty_dirs(base_dir: str = BASE_DIR, exclude_dirs: List[str] = None) -> int:
    """
    Remove empty directories.
    
    Args:
        base_dir: The base directory to start the search
        exclude_dirs: List of directory paths to exclude
        
    Returns:
        Number of directories removed
    """
    if exclude_dirs is None:
        exclude_dirs = []
        
    # Convert to absolute paths
    exclude_dirs = [os.path.abspath(d) for d in exclude_dirs]
    
    logger.info("Cleaning empty directories...")
    count = 0
    
    # Make multiple passes to handle nested empty directories
    while True:
        removed = 0
        for root, dirs, files in os.walk(base_dir, topdown=False):
            if files:
                continue
                
            # Skip if this is the base directory itself
            if os.path.abspath(root) == os.path.abspath(base_dir):
                continue
                
            # Skip if directory is in the exclude list
            if os.path.abspath(root) in exclude_dirs:
                continue
                
            # Check if directory is empty (no files and no subdirectories)
            has_subdirs = False
            for d in dirs:
                dir_path = os.path.join(root, d)
                if os.path.exists(dir_path):
                    has_subdirs = True
                    break
                    
            if not has_subdirs:
                try:
                    os.rmdir(root)
                    logger.info(f"Removed empty directory: {root}")
                    removed += 1
                    count += 1
                except OSError as e:
                    logger.warning(f"Could not remove directory {root}: {e}")
                    
        if removed == 0:
            break
            
    logger.info(f"Removed {count} empty directories")
    return count

def clean_temp_files(config_manager: ConfigManager = None) -> int:
    """
    Remove temporary files.
    
    Args:
        config_manager: ConfigManager instance to get temp directories
        
    Returns:
        Number of files removed
    """
    if config_manager is None:
        config_manager = ConfigManager()
        
    temp_dir = config_manager.get_temp_dir()
    logger.info(f"Cleaning temporary files from {temp_dir}...")
    
    count = 0
    
    # Patterns to identify temporary files and directories
    temp_patterns = [
        "temp_chunks",
        "*.tmp",
        "*.temp"
    ]
    
    # Clean files in temp directory
    if os.path.exists(temp_dir):
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    logger.info(f"Removed temp file: {item_path}")
                    count += 1
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    logger.info(f"Removed temp directory: {item_path}")
                    count += 1
            except Exception as e:
                logger.error(f"Error removing {item_path}: {e}")
    
    # Clean temp_chunks directories throughout the project
    for root, dirs, _ in os.walk(BASE_DIR):
        for dir_name in dirs:
            if dir_name == "temp_chunks":
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed temp_chunks directory: {dir_path}")
                    count += 1
                except Exception as e:
                    logger.error(f"Error removing {dir_path}: {e}")
    
    logger.info(f"Removed {count} temporary files/directories")
    return count

def consolidate_directories(config_manager: ConfigManager = None) -> int:
    """
    Consolidate files into the correct locations based on ConfigManager.
    
    Args:
        config_manager: ConfigManager instance to get directory locations
        
    Returns:
        Number of files moved
    """
    if config_manager is None:
        config_manager = ConfigManager()
        
    logger.info("Consolidating directories...")
    
    # Get the canonical directories from config
    output_dir = config_manager.get_output_dir()
    cache_dir = config_manager.get_cache_dir()
    temp_dir = config_manager.get_temp_dir()
    uploads_dir = config_manager.get('uploads_dir', os.path.join(BASE_DIR, 'data', 'uploads'))
    
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Find other instances of these directories
    count = 0
    duplicate_dirs = set()
    
    # Look for directories with the same name
    for root, dirs, _ in os.walk(BASE_DIR):
        for dir_name in dirs:
            current_path = os.path.join(root, dir_name)
            
            # Skip the canonical directories
            if current_path in [output_dir, cache_dir, temp_dir, uploads_dir]:
                continue
                
            # Check if directory matches one of our target names
            if dir_name == os.path.basename(output_dir):
                duplicate_dirs.add((current_path, output_dir))
            elif dir_name == os.path.basename(cache_dir):
                duplicate_dirs.add((current_path, cache_dir))
            elif dir_name == os.path.basename(temp_dir):
                duplicate_dirs.add((current_path, temp_dir))
            elif dir_name == os.path.basename(uploads_dir):
                duplicate_dirs.add((current_path, uploads_dir))
    
    # Move files from duplicate directories to canonical ones
    for source_dir, target_dir in duplicate_dirs:
        if os.path.exists(source_dir) and source_dir != target_dir:
            try:
                # Move files from source to target
                for item in os.listdir(source_dir):
                    source_item = os.path.join(source_dir, item)
                    target_item = os.path.join(target_dir, item)
                    
                    # Skip if target already exists
                    if os.path.exists(target_item):
                        continue
                        
                    if os.path.isfile(source_item):
                        shutil.copy2(source_item, target_item)
                        os.remove(source_item)
                        logger.info(f"Moved file: {source_item} -> {target_item}")
                        count += 1
                    elif os.path.isdir(source_item):
                        # For directories, we'll need recursion
                        if not os.path.exists(target_item):
                            shutil.copytree(source_item, target_item)
                            shutil.rmtree(source_item)
                            logger.info(f"Moved directory: {source_item} -> {target_item}")
                            count += 1
                        else:
                            # Target exists, need to merge
                            for sub_item in os.listdir(source_item):
                                sub_source = os.path.join(source_item, sub_item)
                                sub_target = os.path.join(target_item, sub_item)
                                if os.path.isfile(sub_source):
                                    if not os.path.exists(sub_target):
                                        shutil.copy2(sub_source, sub_target)
                                        os.remove(sub_source)
                                        logger.info(f"Moved file: {sub_source} -> {sub_target}")
                                        count += 1
            except Exception as e:
                logger.error(f"Error moving files from {source_dir} to {target_dir}: {e}")
    
    logger.info(f"Moved {count} files to their canonical locations")
    return count

def clean_failed_jobs(config_manager: ConfigManager = None) -> int:
    """
    Clean up failed job directories and broken audio files.
    
    Args:
        config_manager: ConfigManager instance to get directory locations
        
    Returns:
        Number of files cleaned up
    """
    if config_manager is None:
        config_manager = ConfigManager()
        
    uploads_dir = config_manager.get('uploads_dir', os.path.join(BASE_DIR, 'data', 'uploads'))
    logger.info(f"Cleaning failed job directories in {uploads_dir}...")
    
    if not os.path.exists(uploads_dir):
        logger.warning(f"Uploads directory does not exist: {uploads_dir}")
        return 0
    
    count = 0
    
    # Check each job directory
    for job_dir in os.listdir(uploads_dir):
        job_path = os.path.join(uploads_dir, job_dir)
        
        # Skip if not a directory
        if not os.path.isdir(job_path):
            continue
            
        # Check if job.json exists
        job_json_path = os.path.join(job_path, 'job.json')
        if not os.path.exists(job_json_path):
            continue
            
        try:
            # Read job.json
            with open(job_json_path, 'r') as f:
                job_data = json.load(f)
                
            # Check if job failed
            job_status = job_data.get('status')
            if job_status == 'failed':
                logger.info(f"Found failed job: {job_dir}")
                
                # Clean broken temp files
                for file_name in os.listdir(job_path):
                    if file_name == 'job.json':
                        continue
                        
                    file_path = os.path.join(job_path, file_name)
                    if os.path.isfile(file_path) and (file_name.endswith(('.tmp', '.temp')) or '_temp' in file_name):
                        try:
                            os.remove(file_path)
                            logger.info(f"Removed broken temp file: {file_path}")
                            count += 1
                        except Exception as e:
                            logger.error(f"Error removing file {file_path}: {e}")
                
                # Check for incomplete audio files
                for file_name in os.listdir(job_path):
                    if file_name.endswith(('.mp3', '.wav', '.m4a')):
                        file_path = os.path.join(job_path, file_name)
                        file_size = os.path.getsize(file_path)
                        
                        # Check if the file is very small (likely corrupted)
                        if file_size < 1024:  # Less than 1KB
                            try:
                                os.remove(file_path)
                                logger.info(f"Removed broken audio file: {file_path}")
                                count += 1
                            except Exception as e:
                                logger.error(f"Error removing file {file_path}: {e}")
                
        except Exception as e:
            logger.error(f"Error processing job directory {job_path}: {e}")
    
    logger.info(f"Cleaned up {count} files from failed jobs")
    return count

def clean_tts_cache() -> int:
    """
    Clear the TTS cache to force regeneration of audio.
    
    Returns:
        Number of cache entries cleared
    """
    logger.info("Cleaning TTS cache...")
    try:
        from src.core.tts.cache import TTSCache
        
        # Create cache instance
        cache = TTSCache()
        
        # Get stats before clearing
        before_stats = cache.get_cache_stats()
        logger.info(f"TTS cache stats before cleaning: {before_stats}")
        
        # Clear the cache
        result = cache.clear_cache(delete_files=True)
        
        logger.info(f"TTS cache cleared: {result['entries_removed']} entries removed, {result['files_deleted']} files deleted, {result['space_freed_mb']} MB freed")
        return result['entries_removed']
        
    except Exception as e:
        logger.error(f"Error clearing TTS cache: {e}")
        return 0

def clean_all(args=None):
    """
    Run all cleanup functions.
    
    Args:
        args: Command line arguments
    """
    config_manager = ConfigManager()
    
    # Run the cleanup functions
    clean_pycache()
    clean_temp_files(config_manager)
    clean_failed_jobs(config_manager)
    clean_tts_cache()  # Added TTS cache cleaning
    consolidate_directories(config_manager)
    clean_empty_dirs(exclude_dirs=[
        config_manager.get_output_dir(),
        config_manager.get_cache_dir(),
        config_manager.get_temp_dir()
    ])

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="DocToAudiobook Cleanup Utility")
    parser.add_argument('--pycache', action='store_true', help='Clean __pycache__ directories')
    parser.add_argument('--empty', action='store_true', help='Clean empty directories')
    parser.add_argument('--temp', action='store_true', help='Clean temporary files')
    parser.add_argument('--consolidate', action='store_true', help='Consolidate directories')
    parser.add_argument('--failed-jobs', action='store_true', help='Clean up failed jobs and broken audio files')
    parser.add_argument('--tts-cache', action='store_true', help='Clear the TTS cache to force regeneration of audio')
    parser.add_argument('--all', action='store_true', help='Run all cleanup operations')
    
    args = parser.parse_args()
    config_manager = ConfigManager()
    
    # If no arguments are provided, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
        
    # Run the specified cleanup functions
    if args.all:
        clean_all(args)
    else:
        if args.pycache:
            clean_pycache()
        if args.temp:
            clean_temp_files(config_manager)
        if args.failed_jobs:
            clean_failed_jobs(config_manager)
        if args.tts_cache:
            clean_tts_cache()
        if args.consolidate:
            consolidate_directories(config_manager)
        if args.empty:
            clean_empty_dirs(exclude_dirs=[
                config_manager.get_output_dir(),
                config_manager.get_cache_dir(),
                config_manager.get_temp_dir()
            ])

if __name__ == "__main__":
    main() 