# tests/unit/test_ffmpeg_utils.py
import pytest
import os
import json
from unittest.mock import patch, MagicMock

# Import directly from the module to avoid circular imports
from src.services.ffmpeg_service import run_ffmpeg_command, get_media_info
from src.api.middlewares.error_handler import ProcessingError

@pytest.fixture
def test_video_path():
    """Fixture that returns a test video path"""
    return '/tmp/test_video.mp4'

@pytest.fixture
def media_info_sample():
    """Fixture that returns a sample media info dictionary"""
    return {
        'format': 'mp4',
        'duration': 10.5,
        'width': 1280,
        'height': 720,
        'video_codec': 'h264',
        'audio_codec': 'aac',
        'bit_rate': 800000,
        'size': 1048576
    }

@patch('subprocess.run')
def test_run_ffmpeg_command_success(mock_subprocess_run, test_video_path):
    """Test that ffmpeg command runs successfully"""
    # Setup the mock
    mock_process = MagicMock()
    mock_process.stdout = "Dummy output"
    mock_process.stderr = ""
    mock_process.returncode = 0
    mock_subprocess_run.return_value = mock_process
    
    # Execute the function
    result = run_ffmpeg_command(['ffmpeg', '-i', test_video_path, test_video_path])
    
    # Assert the results
    assert result['success'] is True
    assert mock_subprocess_run.call_count == 1
    assert 'stdout' in result
    assert 'stderr' in result
    
@patch('subprocess.run')
def test_run_ffmpeg_command_error(mock_subprocess_run, test_video_path):
    """Test that ProcessingError is raised when ffmpeg command fails"""
    # Setup the mock to raise an exception
    mock_subprocess_run.side_effect = Exception("Command failed")
    
    # Execute the function and assert it raises ProcessingError
    with pytest.raises(ProcessingError) as excinfo:
        run_ffmpeg_command(['ffmpeg', '-i', test_video_path, test_video_path])
    
    # Assert that the error message contains information from the original exception
    assert "Command failed" in str(excinfo.value)
    assert mock_subprocess_run.call_count == 1

@patch('subprocess.run')
def test_run_ffmpeg_command_non_zero_exit(mock_subprocess_run, test_video_path):
    """Test that ProcessingError is raised when ffmpeg returns non-zero exit code"""
    # Setup the mock
    mock_process = MagicMock()
    mock_process.stdout = ""
    mock_process.stderr = "Error: File not found"
    mock_process.returncode = 1
    mock_subprocess_run.return_value = mock_process
    
    # Execute the function and assert it raises ProcessingError
    with pytest.raises(ProcessingError) as excinfo:
        run_ffmpeg_command(['ffmpeg', '-i', test_video_path, test_video_path])
    
    # Assert that the error message contains stderr information
    assert "Error: File not found" in str(excinfo.value)
    assert mock_subprocess_run.call_count == 1

@patch('subprocess.run')
@patch('json.loads')
def test_get_media_info(mock_json_loads, mock_subprocess_run, test_video_path, media_info_sample):
    """Test that media info is correctly extracted from ffprobe output"""
    # Setup the mocks
    mock_process = MagicMock()
    mock_process.stdout = '{}'
    mock_process.returncode = 0
    mock_subprocess_run.return_value = mock_process
    
    # Setup the return value for json.loads
    mock_json_loads.return_value = {
        "format": {
            "format_name": "mp4",
            "duration": "10.5",
            "size": "1048576",
            "bit_rate": "800000"
        },
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1280,
                "height": 720,
                "r_frame_rate": "30/1"
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
                "channels": 2,
                "sample_rate": "44100"
            }
        ]
    }
    
    # Execute the function
    result = get_media_info(test_video_path)
    
    # Assert the results
    assert result['format'] == 'mp4'
    assert result['duration'] == 10.5
    assert result['width'] == 1280
    assert result['height'] == 720
    assert result['video_codec'] == 'h264'
    assert result['audio_codec'] == 'aac'
    assert 'bit_rate' in result
    assert mock_subprocess_run.call_count == 1
    assert mock_json_loads.call_count == 1

@patch('os.path.exists')
def test_get_media_info_file_not_found(mock_exists, test_video_path):
    """Test that ProcessingError is raised when the file doesn't exist"""
    # Setup the mock
    mock_exists.return_value = False
    
    # Execute the function and assert it raises ProcessingError
    with pytest.raises(ProcessingError) as excinfo:
        get_media_info(test_video_path)
    
    # Assert that the error message mentions file not found
    assert "not found" in str(excinfo.value).lower()
