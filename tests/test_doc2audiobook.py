import pytest
import os
from src.doc2audiobook import DocToAudiobook
from src.config_manager import ConfigManager

@pytest.fixture
def config_manager():
    return ConfigManager()

@pytest.fixture
def doc2audiobook(config_manager):
    return DocToAudiobook(config_manager)

def test_chunk_splitting(doc2audiobook):
    text = "This is a test. This is another sentence. And one more."
    chunks = doc2audiobook.split_into_chunks(text, max_chars=20)
    assert len(chunks) > 1
    assert all(len(chunk) <= 20 for chunk in chunks)

def test_semantic_analysis(doc2audiobook):
    text = "The quick brown fox jumps over the lazy dog. This is an important sentence."
    analysis = doc2audiobook.analyze_text_semantics(text)
    assert 'important_sentences' in analysis
    assert len(analysis['important_sentences']) > 0

def test_ssml_generation(doc2audiobook):
    text = "This is a heading. This is important content."
    analysis = doc2audiobook.analyze_text_semantics(text)
    ssml = doc2audiobook.generate_ssml_with_emphasis(text, analysis)
    assert "<speak>" in ssml
    assert "<emphasis" in ssml or "<prosody" in ssml

def test_cache_handling(doc2audiobook):
    text = "Test text for caching"
    settings = {"voice": "test-voice", "speed": 1.0}
    
    # Test caching
    cache_file = doc2audiobook.cache.get_cached_audio(text, settings)
    assert cache_file is None
    
    # Test saving to cache
    test_file = "test.mp3"
    doc2audiobook.cache.cache_audio(text, settings, test_file)
    cache_file = doc2audiobook.cache.get_cached_audio(text, settings)
    assert cache_file == test_file

def test_bookmark_creation(doc2audiobook):
    chapter_info = [{"title": "Chapter 1", "content": "Content 1"}]
    chapter_times = [{"start": 0, "end": 100}]
    bookmark_data = doc2audiobook.create_bookmark_data(
        "test-id",
        chapter_info,
        chapter_times
    )
    assert bookmark_data['audiobook_id'] == "test-id"
    assert len(bookmark_data['chapters']) == 1
    assert 'play_history' in bookmark_data 