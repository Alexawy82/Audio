"""
Job Management Module
Handles job processing and status tracking for document to audiobook conversion
"""

import os
import json
import threading
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import uuid
from pathlib import Path
import shutil
import time

from .config_manager import ConfigManager

logger = logging.getLogger(__name__)

class JobManager:
    """
    Job Manager class for handling document conversion jobs
    """

    def __init__(self, db_path=None):
        """
        Initialize the job manager
        
        Args:
            db_path: Path to the database file for storing job information
        """
        # Get database path from config manager if not provided
        if db_path is None:
            config_manager = ConfigManager()
            self.db_path = config_manager.get_database_path()
        else:
            self.db_path = db_path
            
        self.active_jobs = {}  # Dictionary to store active jobs
        self.job_lock = threading.Lock()  # Lock for thread-safe operations on active_jobs
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"JobManager initialized with database path: {self.db_path}")
        
        # Configuration for cleanup
        self.config_manager = ConfigManager()
        self.cleanup_interval = 3600  # Default to hourly cleanup
        self.job_retention_days = 7   # Keep completed jobs for 7 days by default
        self.last_cleanup_time = time.time()
        
        # Start cleanup thread if enabled
        self.cleanup_enabled = True
        if self.cleanup_enabled:
            self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """Start a background thread for periodic cleanup."""
        def cleanup_thread():
            while self.cleanup_enabled:
                current_time = time.time()
                if current_time - self.last_cleanup_time >= self.cleanup_interval:
                    try:
                        self.cleanup_old_jobs()
                        self.last_cleanup_time = current_time
                    except Exception as e:
                        self.logger.error(f"Error in cleanup thread: {e}")
                        
                # Sleep for a while before checking again
                time.sleep(60)  # Check every minute
                
        thread = threading.Thread(target=cleanup_thread)
        thread.daemon = True
        thread.name = "JobCleanupThread"
        thread.start()
        self.logger.info("Started job cleanup thread")

    def create_job(self, input_file: str, output_dir: str, config: Dict[str, Any]) -> str:
        """
        Create a new job
        
        Args:
            input_file: Path to the input document file
            output_dir: Path to the output directory for audio files
            config: Configuration settings for the job
            
        Returns:
            job_id: Unique ID for the created job
        """
        job_id = str(uuid.uuid4())
        
        with self.job_lock:
            job_info = {
                "job_id": job_id,
                "input_file": input_file,
                "output_dir": output_dir,
                "config": config,
                "status": "created",
                "progress": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "completed_at": None,
                "error": None,
                "result": None
            }
            
            self.active_jobs[job_id] = job_info
            self.logger.info(f"Created job {job_id} for file {input_file}")
            
        return job_id
        
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job information."""
        with self.job_lock:
            job = self.active_jobs.get(job_id)
            
        # If job is not in memory, try to load it from the file system
        if job is None:
            # Try to find job in the uploads directory
            try:
                from flask import current_app
                uploads_dir = current_app.config['UPLOAD_FOLDER']
                job_dir = os.path.join(uploads_dir, job_id)
                job_json_path = os.path.join(job_dir, 'job.json')
                
                if os.path.exists(job_json_path):
                    with open(job_json_path, 'r') as f:
                        job = json.load(f)
                        
                    # Add job to active jobs
                    with self.job_lock:
                        self.active_jobs[job_id] = job
            except Exception as e:
                self.logger.error(f"Error loading job {job_id} from file: {e}")
                
        return job
            
    def update_job_status(self, job_id: str, status: str, **kwargs) -> bool:
        """Update job status and additional information."""
        with self.job_lock:
            if job_id not in self.active_jobs:
                self.logger.warning(f"Attempted to update non-existent job {job_id}")
                return False
                
            job = self.active_jobs[job_id]
            job['status'] = status
            
            if status == 'completed':
                job['end_time'] = datetime.now().isoformat()
            elif status == 'failed':
                job['end_time'] = datetime.now().isoformat()
                job['error'] = kwargs.get('error', 'Unknown error')
                
            # Update any additional fields
            for key, value in kwargs.items():
                if key not in ['status', 'error']:
                    job[key] = value
                    
            self.logger.info(f"Updated job {job_id} status to {status}")
            return True
            
    def update_job_progress(self, job_id: str, progress: float, step: str) -> bool:
        """Update job progress and current step."""
        with self.job_lock:
            if job_id not in self.active_jobs:
                return False
                
            job = self.active_jobs[job_id]
            job['progress'] = progress
            job['current_step'] = step
            
            self.logger.debug(f"Job {job_id} progress: {progress}% - {step}")
            return True
            
    def cleanup_job(self, job_id: str) -> bool:
        """Clean up job resources."""
        with self.job_lock:
            if job_id not in self.active_jobs:
                return False
                
            job = self.active_jobs[job_id]
            
            # Remove temporary files if job failed
            if job['status'] == 'failed':
                try:
                    temp_dir = Path(job['output_dir'])
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                except Exception as e:
                    self.logger.error(f"Error cleaning up job {job_id}: {e}")
                    
            # Remove job from active jobs
            del self.active_jobs[job_id]
            
            self.logger.info(f"Cleaned up job {job_id}")
            return True
            
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get information about all jobs."""
        with self.job_lock:
            return list(self.active_jobs.values())
            
    def get_job_files(self, job_id: str) -> List[Dict[str, Any]]:
        """Get list of files generated by a job."""
        job = self.get_job(job_id)
        if not job or 'result' not in job:
            return []
            
        result = job['result']
        if isinstance(result, dict) and 'output_files' in result:
            return result['output_files']
        elif isinstance(result, tuple) and len(result) > 1:
            return result[1]
        return []
        
    def validate_job(self, job_id: str) -> bool:
        """Validate job state and resources."""
        job = self.get_job(job_id)
        if not job:
            return False
            
        # Check input file
        input_file = Path(job['input_file'])
        if not input_file.exists():
            self.logger.error(f"Input file not found for job {job_id}: {input_file}")
            return False
            
        # Check output directory
        output_dir = Path(job['output_dir'])
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True)
            except Exception as e:
                self.logger.error(f"Error creating output directory for job {job_id}: {e}")
                return False
                
        return True

    def cleanup_old_jobs(self, days: int = None) -> Tuple[int, int]:
        """
        Clean up old job files and entries.
        
        Args:
            days: Number of days to keep jobs (None to use default)
            
        Returns:
            Tuple containing (removed_jobs_count, removed_files_count)
        """
        if days is None:
            days = self.job_retention_days
            
        self.logger.info(f"Starting job cleanup for jobs older than {days} days")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        removed_jobs = 0
        removed_files = 0
        
        try:
            # Get list of jobs to clean
            jobs_to_clean = []
            with self.job_lock:
                for job_id, job in list(self.active_jobs.items()):
                    # Check if job is completed or failed
                    if job['status'] not in ['completed', 'failed']:
                        continue
                        
                    # Check job age
                    job_date_str = job.get('completed_at') or job.get('updated_at') or job.get('created_at')
                    if not job_date_str:
                        continue
                        
                    try:
                        job_date = datetime.fromisoformat(job_date_str)
                        if job_date < cutoff_date:
                            jobs_to_clean.append((job_id, job))
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Could not parse date for job {job_id}: {e}")
            
            # Process jobs to clean
            for job_id, job in jobs_to_clean:
                try:
                    # Clean up output directory
                    output_dir = job.get('output_dir')
                    if output_dir and os.path.exists(output_dir) and os.path.isdir(output_dir):
                        # Count files before removal
                        file_count = 0
                        for root, _, files in os.walk(output_dir):
                            file_count += len(files)
                            
                        # Remove directory
                        shutil.rmtree(output_dir)
                        removed_files += file_count
                        self.logger.info(f"Removed job directory: {output_dir} with {file_count} files")
                    
                    # Remove job from active jobs
                    with self.job_lock:
                        if job_id in self.active_jobs:
                            del self.active_jobs[job_id]
                            
                    removed_jobs += 1
                    
                except Exception as e:
                    self.logger.error(f"Error cleaning up job {job_id}: {e}")
                    
            self.logger.info(f"Cleanup completed: removed {removed_jobs} jobs and {removed_files} files")
            return (removed_jobs, removed_files)
            
        except Exception as e:
            self.logger.error(f"Error during job cleanup: {e}")
            return (0, 0)
            
    def cleanup_temp_files(self) -> int:
        """
        Clean up temporary files generated during processing.
        
        Returns:
            Number of files removed
        """
        self.logger.info("Cleaning up temporary files")
        count = 0
        
        try:
            temp_dir = self.config_manager.get_temp_dir()
            
            # Clean the temporary directory
            if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
                for item in os.listdir(temp_dir):
                    item_path = os.path.join(temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                            count += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            count += 1
                    except Exception as e:
                        self.logger.error(f"Error removing temporary item {item_path}: {e}")
            
            # Look for temp_chunks directories in job directories
            for job_id, job in self.active_jobs.items():
                if job['status'] in ['completed', 'failed']:
                    output_dir = job.get('output_dir')
                    if output_dir and os.path.exists(output_dir):
                        temp_chunks_dir = os.path.join(output_dir, 'temp_chunks')
                        if os.path.exists(temp_chunks_dir) and os.path.isdir(temp_chunks_dir):
                            try:
                                shutil.rmtree(temp_chunks_dir)
                                count += 1
                                self.logger.info(f"Removed temp_chunks directory for job {job_id}")
                            except Exception as e:
                                self.logger.error(f"Error removing temp_chunks for job {job_id}: {e}")
                                
            self.logger.info(f"Removed {count} temporary files/directories")
            return count
            
        except Exception as e:
            self.logger.error(f"Error during temporary file cleanup: {e}")
            return 0
            
    def set_cleanup_interval(self, interval_hours: float) -> None:
        """Set the cleanup interval in hours."""
        self.cleanup_interval = interval_hours * 3600  # Convert to seconds
        self.logger.info(f"Cleanup interval set to {interval_hours} hours")
        
    def set_job_retention_days(self, days: int) -> None:
        """Set the number of days to retain completed/failed jobs."""
        self.job_retention_days = days
        self.logger.info(f"Job retention period set to {days} days")
        
    def run_maintenance(self) -> Dict[str, Any]:
        """
        Run full maintenance including job cleanup, temp file cleanup, etc.
        
        Returns:
            Dictionary with results of maintenance operations
        """
        self.logger.info("Running full maintenance")
        results = {}
        
        try:
            # Clean up old jobs
            removed_jobs, removed_files = self.cleanup_old_jobs()
            results['jobs_removed'] = removed_jobs
            results['job_files_removed'] = removed_files
            
            # Clean up temporary files
            temp_files_removed = self.cleanup_temp_files()
            results['temp_files_removed'] = temp_files_removed
            
            # Update last cleanup time
            self.last_cleanup_time = time.time()
            results['success'] = True
            results['timestamp'] = datetime.now().isoformat()
            
            self.logger.info("Maintenance completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during maintenance: {e}")
            results['success'] = False
            results['error'] = str(e)
            return results

# Create global job manager instance
config_manager = ConfigManager()
job_manager = JobManager(config_manager.get_database_path()) 