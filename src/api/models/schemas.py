from typing import Optional, Literal
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
    position: Literal["top_left", "top_right", "bottom_left", "bottom_right"] = "bottom_right"
    scale: float = Field(0.3, ge=0.1, le=1.0)
    webhook_url: Optional[HttpUrl] = None
    id: Optional[str] = None

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
    output_format: Literal["txt", "srt", "vtt", "json"] = "txt"
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

