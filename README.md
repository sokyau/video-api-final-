# Video Processing API

REST API service for video processing operations including adding captions, meme overlays, video concatenation, and animated text.

## Features

- Add captions/subtitles to videos
- Overlay meme images on videos
- Concatenate multiple videos
- Add animated text effects to videos
- Extract audio from media files
- Transcribe audio

## Requirements

- Python 3.9+
- FFmpeg
- Redis server

## Installation

### Using Docker (recommended)

1. Clone the repository:
```bash
git clone https://github.com/sokyau/video-api-final-.git
cd video-api-final-

Configure the environment variables:

bashcp .env.example .env
# Edit .env file with your settings

Build and run with Docker Compose:

bashdocker-compose up -d
Manual Installation

Clone the repository:

bashgit clone https://github.com/sokyau/video-api-final-.git
cd video-api-final-

Create and activate a virtual environment:

bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:

bashpip install -r requirements.txt

Install FFmpeg if not already installed:

Ubuntu/Debian: sudo apt-get install ffmpeg
MacOS: brew install ffmpeg
Windows: Download from FFmpeg website


Configure environment variables:

bashcp .env.example .env
# Edit .env file with your settings

Run the application:

bashpython -m src.wsgi

Run the worker (in a separate terminal):

bashpython -m src.redis_worker
API Endpoints
Video Processing

POST /api/v1/video/caption - Add subtitles to a video
POST /api/v1/video/meme-overlay - Add a meme overlay to a video
POST /api/v1/video/concatenate - Concatenate multiple videos
POST /api/v1/video/animated-text - Add animated text to a video

Media Processing

POST /api/v1/media/extract-audio - Extract audio from a video or media file
POST /api/v1/media/transcribe - Transcribe audio from a media file

Authentication
All API endpoints require API key authentication. Add your API key to the X-API-Key header in all requests.
Development
Running Tests
bashpython -m pytest

## 5. docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
      - ./temp:/app/temp
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
      - DEBUG=True
      - LOG_LEVEL=INFO
      - API_KEY=${API_KEY:-test_api_key}
      - STORAGE_PATH=/app/storage
      - TEMP_DIR=/app/temp
      - LOG_DIR=/app/logs
    depends_on:
      - redis
    command: python -m src.wsgi
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  redis_worker:
    build: .
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
      - ./temp:/app/temp
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
      - DEBUG=True
      - LOG_LEVEL=INFO
      - API_KEY=${API_KEY:-test_api_key}
      - STORAGE_PATH=/app/storage
      - TEMP_DIR=/app/temp
      - LOG_DIR=/app/logs
    depends_on:
      - redis
      - api
    command: python -m src.redis_worker
    restart: unless-stopped

  worker:
    build: .
    volumes:
      - ./storage:/app/storage
      - ./logs:/app/logs
      - ./temp:/app/temp
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
      - DEBUG=True
      - LOG_LEVEL=INFO
      - API_KEY=${API_KEY:-test_api_key}
      - STORAGE_PATH=/app/storage
      - TEMP_DIR=/app/temp
      - LOG_DIR=/app/logs
    depends_on:
      - redis
      - api
    command: python -m src.worker
    restart: unless-stopped

volumes:
  redis_data:


