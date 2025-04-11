"""
Chapter management module for handling chapter detection and organization.
"""

import logging
import re
from typing import Optional, List, Tuple, Dict
import spacy
from spacy.lang.en import English

class ChapterManager:
    """Handles chapter detection and organization."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.nlp = spacy.load("en_core_web_sm")
        
    def detect_chapters(self, text: str, max_chapters: int = 30) -> List[Tuple[str, str]]:
        """
        Detect chapters in text using NLP and pattern matching.
        
        Args:
            text: Input text
            max_chapters: Maximum number of chapters to detect
            
        Returns:
            List of (title, content) tuples
        """
        try:
            self.logger.info(f"Starting chapter detection on text of length {len(text)} chars")
            
            # Validation - make sure we have text to process
            if not text or len(text.strip()) < 100:
                self.logger.warning(f"Text too short ({len(text)} chars) for chapter detection, using entire text")
                return [("Complete Document", text)]
            
            # First try to find explicit chapter markers
            chapters = self._find_explicit_chapters(text)
            
            # If no explicit chapters found, use semantic analysis
            if not chapters:
                self.logger.info("No explicit chapters found, trying semantic analysis")
                chapters = self._detect_semantic_chapters(text, max_chapters)
                
            # If still no chapters, use fallback method
            if not chapters:
                self.logger.info("No semantic chapters found, using fallback method")
                chapters = self._fallback_chapter_detection(text, max_chapters)
            
            # Verify we're capturing all the content
            if chapters:
                total_chapter_chars = sum(len(content) for _, content in chapters)
                original_text_chars = len(text.strip())
                content_ratio = total_chapter_chars / original_text_chars
                
                self.logger.info(f"Detected {len(chapters)} chapters with {total_chapter_chars} chars "
                               f"({content_ratio:.2%} of original {original_text_chars} chars)")
                
                # If we lost more than 10% of content, fall back to a single chapter
                if content_ratio < 0.90:
                    self.logger.warning(f"Content loss in chapter detection: only {content_ratio:.2%} of original text preserved")
                    self.logger.warning("Falling back to single chapter to preserve all content")
                    return [("Complete Document", text)]
            else:
                # No chapters detected - use the entire text
                self.logger.warning("No chapters detected, using entire text")
                return [("Complete Document", text)]
                
            self.logger.info(f"Final chapter count: {len(chapters)}")
            return chapters
            
        except Exception as e:
            self.logger.error(f"Error in chapter detection: {e}")
            # Instead of raising, return the whole text as one chapter
            self.logger.warning("Due to error, falling back to using entire text as one chapter")
            return [("Complete Document", text)]
            
    def _find_explicit_chapters(self, text: str) -> List[Tuple[str, str]]:
        """Find chapters marked with explicit markers."""
        try:
            # Common chapter patterns - expanded to catch more formats
            patterns = [
                r'Chapter\s+\d+[.:]\s*([^\n]+)',       # Chapter 1: Title
                r'CHAPTER\s+\d+[.:]\s*([^\n]+)',       # CHAPTER 1: Title (all caps)
                r'^\s*\d+\.\s*([^\n]+)',               # 1. Title (with possible indent)
                r'^\s*[IVX]+\.\s*([^\n]+)',            # I. Title (with possible indent)
                r'^\s*[A-Z]\.\s*([^\n]+)',             # A. Title (with possible indent)
                r'^\s*PART\s+\d+[.:]\s*([^\n]+)',      # PART 1: Title
                r'^\s*Part\s+\d+[.:]\s*([^\n]+)',      # Part 1: Title
                r'^\s*SECTION\s+\d+[.:]\s*([^\n]+)',   # SECTION 1: Title
                r'^\s*Section\s+\d+[.:]\s*([^\n]+)',   # Section 1: Title
                r'^\s*\d+\s+([A-Z][^\n]+)',            # 1 TITLE (number followed by all caps title)
                r'^\s*[A-Z][A-Z\s]+$'                  # ALL CAPS LINE (likely a chapter title)
            ]
            
            self.logger.info(f"Searching for explicit chapter patterns in text of length {len(text)}")
            
            # Get all potential chapter markers and sort by position
            all_matches = []
            
            for pattern_idx, pattern in enumerate(patterns):
                for match in re.finditer(pattern, text, re.MULTILINE):
                    # For the last pattern (ALL CAPS), use the whole match as title
                    if pattern_idx == len(patterns) - 1:
                        title = match.group(0).strip()
                    else:
                        # For other patterns, use the captured group
                        try:
                            title = match.group(1).strip()
                        except IndexError:
                            title = match.group(0).strip()
                    
                    all_matches.append({
                        'title': title,
                        'start': match.start(),
                        'end': match.end(),
                        'pattern': pattern
                    })
            
            # Sort matches by position in text
            all_matches.sort(key=lambda x: x['start'])
            
            # Process matches into chapters
            chapters = []
            
            for i, match in enumerate(all_matches):
                start = match.get('end')
                
                # Find the end of this chapter (start of next chapter or end of text)
                if i < len(all_matches) - 1:
                    end = all_matches[i + 1].get('start')
                else:
                    end = len(text)
                    
                # Extract chapter content
                content = text[start:end].strip()
                
                # Skip if no content
                if not content:
                    continue
                    
                # Add to chapters
                title = match.get('title')
                chapters.append((title, content))
                self.logger.debug(f"Found explicit chapter: '{title}' with {len(content)} chars")
            
            self.logger.info(f"Found {len(chapters)} explicit chapters")
            return chapters
            
        except Exception as e:
            self.logger.error(f"Error finding explicit chapters: {e}")
            return []
            
    def _detect_semantic_chapters(self, text: str, max_chapters: int) -> List[Tuple[str, str]]:
        """Detect chapters using semantic analysis."""
        try:
            # For very short texts, don't bother with semantic analysis
            if len(text) < 5000:  # Less than ~1 page
                self.logger.info(f"Text too short ({len(text)} chars) for semantic chapter detection")
                return []
                
            # Use a smaller chunk of text for very large documents to avoid memory issues with spaCy
            # and speed up processing
            text_to_process = text
            original_length = len(text)
            sample_ratio = 1.0
            
            if len(text) > 1000000:  # 1MB
                # For very large texts, just examine beginning, middle and end sections
                sample_ratio = 0.3  # Process 30%
                sample_size = int(len(text) * sample_ratio)
                beginning = text[:sample_size//3]
                middle_start = max(0, len(text)//2 - sample_size//6)
                middle = text[middle_start:middle_start + sample_size//3]
                end = text[-sample_size//3:]
                text_to_process = beginning + middle + end
                self.logger.info(f"Text too large ({original_length} chars), using {len(text_to_process)} char sample for semantic analysis")
            
            # Create a more limited tokenization pipeline to improve performance
            # Parse a manageable number of sentences
            max_sentences = 5000  # Limit sentences to prevent memory issues
            if len(text_to_process) > 200000:  # For larger texts, use a sentence tokenizer only
                sentencizer = English()
                sentencizer.add_pipe("sentencizer")
                doc = sentencizer(text_to_process)
            else:
                doc = self.nlp(text_to_process)
                
            sentences = list(doc.sents)
            if len(sentences) > max_sentences:
                # Take evenly distributed sample
                step = len(sentences) // max_sentences
                sentences = [sentences[i] for i in range(0, len(sentences), step)]
                
            self.logger.info(f"Running semantic chapter detection on {len(sentences)} sentences")
            
            # Score sentences based on length and content
            scores = []
            for i, sent in enumerate(sentences):
                # Base score starts low
                score = 10  # Base score
                
                # Increase score based on sentence length (but not too much)
                length_score = min(len(sent.text), 50)  # Cap at 50
                score += length_score
                
                # Apply various bonuses to identify potential chapter breaks
                # Bonus for being at start of paragraph
                if i > 0 and '\n\n' in sent.text or (i > 0 and sentences[i-1].text.endswith('\n')):
                    score *= 1.5
                    
                # Significant bonus for all caps (likely a title)
                if sent.text.strip().isupper():
                    score *= 3.0
                    
                # Large bonus for chapter-like phrases
                if re.search(r'chapter|part|section|volume|book', sent.text.lower()):
                    score *= 3.0
                    
                # Bonus for numbered patterns that look like chapter headings
                if re.search(r'^\s*(\d+|[ivxlcdm]+|[IVXLCDM]+)\.?\s+\w+', sent.text):
                    score *= 2.5
                    
                # Bonus for short sentences (likely titles)
                if 10 < len(sent.text.strip()) < 60:
                    score *= 1.5
                    
                # Penalize very long sentences (unlikely to be chapter titles)
                if len(sent.text.strip()) > 200:
                    score *= 0.5
                    
                scores.append(score)
            
            if not scores:
                self.logger.warning("No sentences found for scoring in semantic chapter detection")
                return []
                
            # Find potential chapter starts with improved algorithm
            chapter_starts = []
            
            # First, find very obvious chapter breaks (highest scoring sentences)
            high_threshold = max(scores) * 0.7  # 70% of max score
            for i, score in enumerate(scores):
                if score > high_threshold:
                    chapter_starts.append(i)
                    
            # If we didn't find enough chapter breaks, look for local peaks
            if len(chapter_starts) < max_chapters * 0.5:
                avg_score = sum(scores) / len(scores)
                # Find sentences that are local peaks and significantly above average
                for i in range(1, len(sentences)-1):
                    if (scores[i] > scores[i-1] * 1.3 and 
                        scores[i] > scores[i+1] * 1.3 and
                        scores[i] > avg_score * 1.5):
                        if i not in chapter_starts:
                            chapter_starts.append(i)
            
            # Ensure we have at least some chapters if text is long enough
            if len(chapter_starts) < 3 and len(text) > 50000:
                self.logger.info("Using evenly distributed chapters as fallback")
                # Fall back to evenly distributed chapters
                chapter_count = min(max_chapters, max(3, len(text) // 20000))
                step = len(sentences) // chapter_count
                chapter_starts = [i for i in range(0, len(sentences), step)]
                    
            # Limit number of chapters and sort by position
            if len(chapter_starts) > max_chapters:
                chapter_starts = sorted(chapter_starts, 
                                     key=lambda x: scores[x], 
                                     reverse=True)[:max_chapters]
            
            # Always sort by position in text
            chapter_starts.sort()
                
            self.logger.info(f"Found {len(chapter_starts)} potential chapter starts")
            
            # If we're using a sample of the original text, map the sentence positions back to the full text
            if sample_ratio < 1.0:
                self.logger.info("Mapping chapter breaks from sample back to full text")
                # We need to map these positions back to the original text
                # This is approximate since we can't exactly map samples
                mapped_positions = []
                
                # Simple mapping based on relative position in the sample
                for pos in chapter_starts:
                    relative_pos = pos / len(sentences)
                    full_text_pos = int(relative_pos * original_length)
                    
                    # Find a good break point near this position in the full text
                    # Look for paragraph breaks or sentence ends
                    search_window = 1000  # 1000 chars for search
                    search_start = max(0, full_text_pos - search_window//2)
                    search_end = min(len(text), full_text_pos + search_window//2)
                    
                    # Try to find a paragraph break
                    para_break = text.find('\n\n', search_start, search_end)
                    if para_break != -1:
                        mapped_positions.append(para_break + 2)
                    else:
                        # Try to find a sentence end
                        for end_marker in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                            sent_end = text.find(end_marker, search_start, search_end)
                            if sent_end != -1:
                                mapped_positions.append(sent_end + len(end_marker))
                                break
                        else:
                            # Fallback to approximate position
                            mapped_positions.append(full_text_pos)
                
                # Use the mapped positions to create chapters directly from original text
                chapters = []
                mapped_positions.sort()  # Ensure positions are in order
                
                for i, start_pos in enumerate(mapped_positions):
                    end_pos = mapped_positions[i+1] if i+1 < len(mapped_positions) else len(text)
                    
                    # Extract content
                    content = text[start_pos:end_pos].strip()
                    
                    # Extract title from first line
                    lines = content.split('\n', 1)
                    title = lines[0].strip()
                    if len(title) > 100:  # Title too long, create generic one
                        title = f"Chapter {i+1}"
                    
                    if content:
                        chapters.append((title, content))
                        self.logger.debug(f"Created mapped chapter {i+1} with title '{title}' and {len(content)} chars")
                
                return chapters
                    
            # Create chapters from the original sentences
            chapters = []
            for i, start_idx in enumerate(chapter_starts):
                start = start_idx
                end = chapter_starts[i+1] if i+1 < len(chapter_starts) else len(sentences)
                
                # Use the sentence at the chapter start as the title
                title = sentences[start].text.strip()
                
                # If title is too long, create a shorter one
                if len(title) > 100:
                    title = f"Chapter {i+1}"
                
                # Include the title sentence in the content for consistency
                content = ' '.join(s.text for s in sentences[start:end])
                
                if content.strip():
                    chapters.append((title, content))
                    self.logger.debug(f"Created semantic chapter with title '{title}' and {len(content)} chars")
            
            # Verify we haven't lost content
            total_content = sum(len(content) for _, content in chapters)
            if total_content < len(text_to_process) * 0.9:  # Lost more than 10%
                self.logger.warning(f"Semantic chapter detection lost content: {len(text_to_process)} vs {total_content}")
                return []  # Let fallback method handle it
                    
            return chapters
            
        except Exception as e:
            self.logger.error(f"Error in semantic chapter detection: {e}")
            return []
            
    def _fallback_chapter_detection(self, text: str, max_chapters: int) -> List[Tuple[str, str]]:
        """Fallback method for chapter detection when no explicit chapters are found."""
        try:
            self.logger.info(f"Using fallback chapter detection for text of length {len(text)}")
            
            # Handle empty or very short text
            if not text or len(text) < 100:
                self.logger.warning("Text is empty or very short, creating single chapter")
                return [("Complete Document", text)]
                
            # For reasonable-sized documents, create a small number of chapters
            total_chars = len(text)
            
            # For very small documents, just use a single chapter
            if total_chars < 20000:  # ~4 pages
                self.logger.info(f"Small document detected ({total_chars} chars), using single chapter")
                return [("Complete Document", text)]
            
            # For very large documents, ensure we have enough chapters
            if total_chars > 500000 and max_chapters < 20:  # 500KB of text
                self.logger.info(f"Large document detected ({total_chars} chars), increasing max chapters")
                max_chapters = max(max_chapters, 20)  # Ensure at least 20 chapters for very large docs
                
            # Use an algorithm for calculating target chapter size based on document length
            # For large documents, we want more chapters to keep each chapter manageable
            if total_chars < 50000:  # ~10 pages
                num_chapters = min(3, max_chapters)
            elif total_chars < 200000:  # ~40 pages
                num_chapters = min(5, max_chapters)
            elif total_chars < 500000:  # ~100 pages
                num_chapters = min(10, max_chapters)
            else:  # very large document
                num_chapters = min(max_chapters, max(15, total_chars // 50000))
                
            self.logger.info(f"Creating {num_chapters} chapters for document of size {total_chars} chars")
            
            target_chapter_size = total_chars // num_chapters
            self.logger.info(f"Target chapter size: {target_chapter_size} chars")
            
            # Create chapters
            chapters = []
            current_pos = 0
            chapter_num = 1
            
            while current_pos < len(text) and len(chapters) < max_chapters:
                # Calculate where the next chapter should end
                next_pos = min(current_pos + target_chapter_size, len(text))
                
                # If we're not at the end, find a good breakpoint
                if next_pos < len(text) - 100:  # Leave room to find a good breakpoint
                    # Try to find paragraph breaks first (most natural)
                    paragraph_end = text.find('\n\n', next_pos - 500, next_pos + 500)
                    if paragraph_end != -1:
                        next_pos = paragraph_end + 2
                    else:
                        # Try to find sentence ends
                        found_break = False
                        for end_marker in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
                            sentence_end = text.find(end_marker, next_pos - 300, next_pos + 300)
                            if sentence_end != -1:
                                next_pos = sentence_end + len(end_marker)
                                found_break = True
                                break
                        
                        # If no sentence break found, try to find a space
                        if not found_break:
                            space = text.find(' ', next_pos - 100, next_pos + 100)
                            if space != -1:
                                next_pos = space + 1
                
                # Make sure we're making progress
                if next_pos <= current_pos:
                    next_pos = min(current_pos + 1000, len(text))  # Ensure we advance at least a bit
                    self.logger.warning(f"Couldn't find natural break point, advancing {next_pos - current_pos} chars")
                
                # Extract chapter content
                chapter_content = text[current_pos:next_pos].strip()
                
                # Validate content length - skip tiny fragments but ensure we don't lose content
                if len(chapter_content) < 50 and chapter_num > 1 and current_pos > len(text) - 100:
                    self.logger.warning(f"Chapter {chapter_num} is too short ({len(chapter_content)} chars) and near end, skipping")
                    # We've reached the end with a small fragment - add to previous chapter if possible
                    if chapters:
                        prev_title, prev_content = chapters[-1]
                        chapters[-1] = (prev_title, f"{prev_content}\n\n{chapter_content}")
                    break
                
                # Create a meaningful title
                first_lines = chapter_content.split('\n', 2)
                potential_title = first_lines[0].strip()
                
                # Check if the first line looks like a title
                if (len(potential_title) < 100 and 
                    (potential_title.isupper() or 
                     potential_title.startswith("Chapter") or
                     potential_title.startswith("CHAPTER") or
                     potential_title.startswith("Part") or
                     potential_title.startswith("PART") or
                     potential_title.startswith("Section") or
                     potential_title.startswith("SECTION"))):
                    # Use the first line as the title
                    title = potential_title
                    # Remove the title from the content only if it's repeated
                    # This ensures we don't lose content
                    if chapter_content.startswith(potential_title) and chapter_content.count(potential_title) > 1:
                        chapter_content = chapter_content[len(potential_title):].strip()
                else:
                    # Create a generic title with excerpt
                    first_line = potential_title[:50].strip()
                    if len(first_line) > 30:
                        title = f"Part {chapter_num}: {first_line[:30]}..."
                    else:
                        title = f"Part {chapter_num}: {first_line}"
                
                # Add chapter (use updated chapter_content if title was extracted)
                if chapter_content:
                    chapters.append((title, chapter_content))
                    self.logger.debug(f"Created chapter {chapter_num} with {len(chapter_content)} chars and title '{title}'")
                else:
                    self.logger.warning(f"Empty chapter content after processing for chapter {chapter_num}, skipping")
                
                # Move to next position
                current_pos = next_pos
                chapter_num += 1
            
            # CRITICAL: Always check if we have remaining text and add it as a final chapter
            if current_pos < len(text):
                remaining = text[current_pos:].strip()
                if remaining:
                    self.logger.info(f"Adding final chapter with remaining {len(remaining)} chars")
                    chapters.append((f"Part {chapter_num}: Final Section", remaining))
            
            # Validate results
            if not chapters:
                self.logger.error("No chapters created in fallback detection!")
                return [("Complete Document", text)]  # Return the entire document as one chapter
                
            total_content = sum(len(content) for _, content in chapters)
            self.logger.info(f"Created {len(chapters)} chapters with total {total_content} chars (original text: {len(text.strip())} chars)")
            
            # Check if we lost content (more than 5%)
            content_ratio = total_content / len(text.strip()) if text.strip() else 0
            self.logger.info(f"Content preservation ratio: {content_ratio:.2f}")
            
            if content_ratio < 0.95:  # If we lost more than 5% of content
                self.logger.warning(f"Content loss detected! Original: {len(text.strip())}, Chapters: {total_content}")
                # Fall back to simple chunking with higher chapter count for very large texts
                if total_chars > 500000 and num_chapters < 30:
                    self.logger.info("Retrying with more chapters for large document")
                    return self._fallback_chapter_detection(text, max(30, max_chapters))
                else:
                    # Fall back to a single chapter if we still lost content
                    self.logger.info("Falling back to single chapter")
                    return [("Complete Document", text)]
            
            # Success case
            if len(chapters) == 1:
                # If we only created one chapter, give it a better title
                chapters[0] = ("Complete Document", chapters[0][1])
                
            return chapters
            
        except Exception as e:
            self.logger.error(f"Error in fallback chapter detection: {e}")
            # Return the whole text as a single chapter in case of errors
            return [("Complete Document", text)] 