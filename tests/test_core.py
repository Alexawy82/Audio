"""
Test suite for core modules.
"""

import os
import json
import tempfile
import unittest
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from src.core.user_manager import UserManager
from src.core.job_queue import JobQueue
from src.core.cache_manager import TTSCache
from src.core.document_processor import DocumentProcessor
from src.core.audio_processor import AudioProcessor
from src.core.chapter_manager import ChapterManager
from src.core.bookmark_manager import BookmarkManager

class TestUserManager(unittest.TestCase):
    """Tests for UserManager."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "users.db")
        self.user_manager = UserManager(db_path=self.db_path)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_create_user(self):
        success, message = self.user_manager.create_user(
            "testuser", "test@example.com", "password123"
        )
        self.assertTrue(success)
        self.assertEqual(message, "User created successfully")
        
    def test_duplicate_user(self):
        self.user_manager.create_user("testuser", "test@example.com", "password123")
        success, message = self.user_manager.create_user(
            "testuser", "test2@example.com", "password123"
        )
        self.assertFalse(success)
        self.assertEqual(message, "Username or email already exists")
        
    def test_authenticate_user(self):
        self.user_manager.create_user("testuser", "test@example.com", "password123")
        success, message, token_data = self.user_manager.authenticate_user(
            "testuser", "password123"
        )
        self.assertTrue(success)
        self.assertIsNotNone(token_data)
        self.assertIn('token', token_data)
        
    def test_invalid_credentials(self):
        success, message, token_data = self.user_manager.authenticate_user(
            "testuser", "wrongpassword"
        )
        self.assertFalse(success)
        self.assertIsNone(token_data)
        
class TestJobQueue(unittest.TestCase):
    """Tests for JobQueue."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "jobs.db")
        self.job_queue = JobQueue(db_path=self.db_path, max_workers=1)
        
    def tearDown(self):
        self.job_queue.stop()
        shutil.rmtree(self.temp_dir)
        
    def test_submit_job(self):
        job_id = self.job_queue.submit_job(
            "test_job",
            {"data": "test"},
            priority=1
        )
        self.assertIsNotNone(job_id)
        
    def test_get_job_status(self):
        job_id = self.job_queue.submit_job(
            "test_job",
            {"data": "test"}
        )
        status = self.job_queue.get_job_status(job_id)
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'pending')
        
    def test_job_processing(self):
        def test_handler(data):
            return {"result": "processed"}
            
        self.job_queue.register_handler("test_job", test_handler)
        job_id = self.job_queue.submit_job(
            "test_job",
            {"data": "test"}
        )
        
        # Wait for processing
        time.sleep(1)
        
        status = self.job_queue.get_job_status(job_id)
        self.assertEqual(status['status'], 'completed')
        self.assertEqual(status['result'], {"result": "processed"})
        
class TestTTSCache(unittest.TestCase):
    """Tests for TTSCache."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = os.path.join(self.temp_dir, "cache")
        self.db_path = os.path.join(self.temp_dir, "cache.db")
        self.cache = TTSCache(cache_dir=self.cache_dir, db_path=self.db_path)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_cache_audio(self):
        text = "Test text"
        voice_settings = {"voice": "test"}
        audio_file = os.path.join(self.temp_dir, "test.mp3")
        
        # Create dummy audio file
        with open(audio_file, 'w') as f:
            f.write("dummy audio data")
            
        success = self.cache.cache_audio(text, voice_settings, audio_file)
        self.assertTrue(success)
        
    def test_get_cached_audio(self):
        text = "Test text"
        voice_settings = {"voice": "test"}
        audio_file = os.path.join(self.temp_dir, "test.mp3")
        
        # Create dummy audio file
        with open(audio_file, 'w') as f:
            f.write("dummy audio data")
            
        self.cache.cache_audio(text, voice_settings, audio_file)
        cached_file = self.cache.get_cached_audio(text, voice_settings)
        self.assertEqual(cached_file, audio_file)
        
class TestDocumentProcessor(unittest.TestCase):
    """Tests for DocumentProcessor."""
    
    def setUp(self):
        self.processor = DocumentProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_extract_text(self):
        # Create test document
        doc_path = os.path.join(self.temp_dir, "test.docx")
        # Add test document creation code here
        
        text = self.processor.extract_text(doc_path)
        self.assertIsNotNone(text)
        self.assertGreater(len(text), 0)
        
class TestAudioProcessor(unittest.TestCase):
    """Tests for AudioProcessor."""
    
    def setUp(self):
        self.processor = AudioProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_generate_speed_variants(self):
        # Create test audio file
        input_file = os.path.join(self.temp_dir, "test.mp3")
        # Add test audio file creation code here
        
        output_files = self.processor.generate_speed_variants(
            input_file,
            self.temp_dir,
            speeds=[0.8, 1.0, 1.2]
        )
        self.assertEqual(len(output_files), 3)
        
class TestChapterManager(unittest.TestCase):
    """Tests for ChapterManager."""
    
    def setUp(self):
        self.manager = ChapterManager()
        
    def test_detect_chapters(self):
        text = """
        Chapter 1: Introduction
        This is the first chapter.
        
        Chapter 2: Main Content
        This is the second chapter.
        """
        
        chapters = self.manager.detect_chapters(text)
        self.assertEqual(len(chapters), 2)
        self.assertEqual(chapters[0][0], "Chapter 1: Introduction")
        
class TestBookmarkManager(unittest.TestCase):
    """Tests for BookmarkManager."""
    
    def setUp(self):
        self.manager = BookmarkManager()
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_create_bookmark_data(self):
        bookmark_data = self.manager.create_bookmark_data(
            "test_book",
            [{"title": "Chapter 1", "content": "Content 1"}],
            [{"start": 0, "end": 100}]
        )
        self.assertIsNotNone(bookmark_data)
        self.assertEqual(bookmark_data['audiobook_id'], "test_book")
        
if __name__ == '__main__':
    unittest.main() 