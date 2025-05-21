from typing import Optional, Literal, List
from pydantic import BaseModel, HttpUrl, constr, Field, validator

class VideoCaptionSchema(BaseModel):
    video_url: HttpUrl
    subtitles_url: HttpUrl
    font: Optional[str] = "Arial"
    font_size: Optional[int] = Field(24, ge=12, le=72)
    position: Optional[Literal["top", "bottom", "center"]] = "bottom"
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "video_url": "https://example.com/video.mp4",
                "subtitles_url": "https://example.com/subtitles.srt",
                "font": "Arial",
                "font_size": 24,
                "position": "bottom"
            }
        }

class MemeOverlaySchema(BaseModel):
    video_url: HttpUrl
    meme_url: HttpUrl
    position: Optional[str] = "bottom_right"
    scale: float = Field(0.3, ge=0.1, le=1.0)
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    @validator('position')
    def validate_position(cls, v):
        return v

    class Config:
        schema_extra = {
            "example": {
                "video_url": "https://example.com/video.mp4",
                "meme_url": "https://example.com/meme.png",
                "position": "bottom_right",
                "scale": 0.3
            }
        }

class MediaToMp3Schema(BaseModel):
    media_url: HttpUrl
    bitrate: Optional[constr(regex=r"^[0-9]+k$")] = "192k"
    format: Optional[Literal["mp3", "wav", "aac", "flac"]] = "mp3"
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "media_url": "https://example.com/media.mp4",
                "bitrate": "192k"
            }
        }

class TranscribeMediaSchema(BaseModel):
    media_url: HttpUrl
    language: Optional[constr(min_length=2, max_length=5)] = "auto"
    output_format: Optional[Literal["txt", "srt", "vtt", "json"]] = "txt"
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    @validator('language')
    def validate_language_code(cls, v):
        if v != "auto" and len(v) not in [2, 5]:
            raise ValueError('Language code must be "auto" or a valid ISO code (2 or 5 characters)')
        return v

    class Config:
        schema_extra = {
            "example": {
                "media_url": "https://example.com/media.mp4",
                "language": "en",
                "output_format": "txt"
            }
        }

class AnimatedTextSchema(BaseModel):
    video_url: HttpUrl
    text: str
    animation: Optional[Literal["fade", "slide", "zoom", "typewriter", "bounce"]] = "fade"
    position: Optional[Literal["top", "bottom", "center"]] = "bottom"
    font: Optional[str] = "Arial"
    font_size: Optional[int] = Field(36, ge=12, le=120)
    color: Optional[str] = "white"
    duration: Optional[float] = Field(3.0, ge=1.0, le=20.0)
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "video_url": "https://example.com/video.mp4",
                "text": "Sample Text",
                "animation": "fade",
                "position": "bottom",
                "font": "Arial",
                "font_size": 36,
                "color": "white",
                "duration": 3.0
            }
        }

class ConcatenateVideosSchema(BaseModel):
    video_urls: List[HttpUrl]
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    @validator('video_urls')
    def validate_video_urls(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 videos are required for concatenation')
        return v

    class Config:
        schema_extra = {
            "example": {
                "video_urls": [
                    "https://example.com/video1.mp4",
                    "https://example.com/video2.mp4"
                ]
            }
        }

class ThumbnailSchema(BaseModel):
    video_url: HttpUrl
    time: Optional[float] = 0.0
    width: Optional[int] = Field(640, ge=32, le=3840)
    height: Optional[int] = Field(360, ge=32, le=2160)
    quality: Optional[int] = Field(90, ge=1, le=100)
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "video_url": "https://example.com/video.mp4",
                "time": 5.0,
                "width": 640,
                "height": 360,
                "quality": 90
            }
        }

class ImageOverlaySchema(BaseModel):
    video_url: HttpUrl
    image_url: HttpUrl
    position: Optional[str] = "bottom_right"
    scale: Optional[float] = Field(0.3, ge=0.1, le=1.0)
    opacity: Optional[float] = Field(1.0, ge=0.0, le=1.0)
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    @validator('position')
    def validate_position(cls, v):
        return v

    class Config:
        schema_extra = {
            "example": {
                "video_url": "https://example.com/video.mp4",
                "image_url": "https://example.com/overlay.png",
                "position": "bottom_right",
                "scale": 0.3,
                "opacity": 1.0
            }
        }

class AddAudioSchema(BaseModel):
    video_url: HttpUrl
    audio_url: HttpUrl
    replace_audio: Optional[bool] = True
    audio_volume: Optional[float] = Field(1.0, ge=0.0, le=10.0)
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "video_url": "https://example.com/video.mp4",
                "audio_url": "https://example.com/audio.mp3",
                "replace_audio": True,
                "audio_volume": 1.0
            }
        }
