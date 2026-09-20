"""Tests for transcription module."""

import pytest
from pathlib import Path

from video_agent.transcription.interfaces import (
    Transcript,
    TranscriptSegment,
    TranscriptionError,
)


class TestTranscriptSegment:
    """Test TranscriptSegment model."""
    
    def test_create_segment(self):
        """Test creating a basic segment."""
        segment = TranscriptSegment(
            start=0.0,
            end=5.0,
            text="Hello world"
        )
        
        assert segment.start == 0.0
        assert segment.end == 5.0
        assert segment.text == "Hello world"
        assert segment.confidence is None
    
    def test_create_segment_with_confidence(self):
        """Test creating segment with confidence score."""
        segment = TranscriptSegment(
            start=10.5,
            end=15.2,
            text="Test text",
            confidence=0.95
        )
        
        assert segment.confidence == 0.95
    
    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        # Valid confidence
        segment = TranscriptSegment(
            start=0, end=1, text="test", confidence=0.5
        )
        assert segment.confidence == 0.5
        
        # Invalid confidence should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            TranscriptSegment(
                start=0, end=1, text="test", confidence=1.5
            )


class TestTranscript:
    """Test Transcript model."""
    
    def test_create_empty_transcript(self):
        """Test creating empty transcript."""
        transcript = Transcript(
            language="en",
            duration=0.0
        )
        
        assert transcript.language == "en"
        assert transcript.duration == 0.0
        assert transcript.segments == []
        assert transcript.full_text == ""
    
    def test_create_transcript_with_segments(self):
        """Test creating transcript with segments."""
        segments = [
            TranscriptSegment(start=0.0, end=2.0, text="Hello"),
            TranscriptSegment(start=2.0, end=4.0, text="World"),
        ]
        
        transcript = Transcript(
            language="en",
            duration=4.0,
            segments=segments
        )
        
        assert len(transcript.segments) == 2
        assert transcript.full_text == "Hello World"
    
    def test_full_text_concatenation(self):
        """Test full_text property concatenates segments."""
        segments = [
            TranscriptSegment(start=0, end=1, text="First"),
            TranscriptSegment(start=1, end=2, text="Second"),
            TranscriptSegment(start=2, end=3, text="Third"),
        ]
        
        transcript = Transcript(
            language="en",
            duration=3.0,
            segments=segments
        )
        
        assert transcript.full_text == "First Second Third"
    
    def test_get_segment_at(self):
        """Test getting segment at specific timestamp."""
        segments = [
            TranscriptSegment(start=0.0, end=5.0, text="First segment"),
            TranscriptSegment(start=5.0, end=10.0, text="Second segment"),
            TranscriptSegment(start=10.0, end=15.0, text="Third segment"),
        ]
        
        transcript = Transcript(
            language="en",
            duration=15.0,
            segments=segments
        )
        
        # Find segment in middle
        seg = transcript.get_segment_at(7.5)
        assert seg is not None
        assert seg.text == "Second segment"
        
        # Find segment at start
        seg = transcript.get_segment_at(0.0)
        assert seg is not None
        assert seg.text == "First segment"
        
        # No segment at this time
        seg = transcript.get_segment_at(20.0)
        assert seg is None
    
    def test_get_segments_in_range(self):
        """Test getting segments within time range."""
        segments = [
            TranscriptSegment(start=0.0, end=5.0, text="Segment 1"),
            TranscriptSegment(start=5.0, end=10.0, text="Segment 2"),
            TranscriptSegment(start=10.0, end=15.0, text="Segment 3"),
            TranscriptSegment(start=15.0, end=20.0, text="Segment 4"),
        ]
        
        transcript = Transcript(
            language="en",
            duration=20.0,
            segments=segments
        )
        
        # Get middle segments
        range_segments = transcript.get_segments_in_range(5.0, 15.0)
        assert len(range_segments) == 2
        assert range_segments[0].text == "Segment 2"
        assert range_segments[1].text == "Segment 3"
        
        # Get all segments
        range_segments = transcript.get_segments_in_range(0.0, 20.0)
        assert len(range_segments) == 4
        
        # Get no segments
        range_segments = transcript.get_segments_in_range(25.0, 30.0)
        assert len(range_segments) == 0
    
    def test_metadata_storage(self):
        """Test metadata dictionary storage."""
        metadata = {
            "model": "whisper-base",
            "source_file": "/path/to/audio.wav",
            "processing_time": 12.5
        }
        
        transcript = Transcript(
            language="en",
            duration=10.0,
            metadata=metadata
        )
        
        assert transcript.metadata["model"] == "whisper-base"
        assert transcript.metadata["source_file"] == "/path/to/audio.wav"


class TestTranscriptionError:
    """Test TranscriptionError exception."""
    
    def test_create_error_basic(self):
        """Test creating basic error."""
        error = TranscriptionError("Something went wrong")
        
        assert error.message == "Something went wrong"
        assert error.provider is None
    
    def test_create_error_with_provider(self):
        """Test creating error with provider name."""
        error = TranscriptionError(
            "API timeout",
            provider="Whisper API"
        )
        
        assert error.message == "API timeout"
        assert error.provider == "Whisper API"
    
    def test_error_string_representation(self):
        """Test error string representation."""
        error = TranscriptionError("Test error", provider="TestProvider")
        
        assert str(error) == "Test error"
