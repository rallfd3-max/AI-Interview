"""Validated settings; relative paths are resolved from the project root."""
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    app_host: str = '0.0.0.0'
    app_port: int = Field(8000, ge=1, le=65535)
    debug: bool = True
    database_url: str = 'sqlite:///./data/database/face.db'
    face_model_name: str = 'buffalo_l'
    face_model_root: Path = ROOT / 'data/face_models'
    face_device: Literal['cpu', 'cuda'] = 'cpu'
    allow_model_download: bool = False
    face_match_threshold: float = Field(0.65, ge=-1, le=1)
    face_match_top_k: int = Field(3, ge=1, le=500)
    person_score_strategy: Literal['max', 'mean', 'top_n_mean'] = 'max'
    person_score_top_n: int = Field(2, ge=1, le=5)
    stable_frame_count: int = Field(3, ge=1, le=30)
    session_timeout_seconds: float = Field(10, gt=0)
    max_image_size_mb: float = Field(8, gt=0)
    max_image_pixels: int = Field(20_000_000, gt=0)
    return_debug_info: bool = True
    save_debug_images: bool = False
    allow_multiple_faces: bool = False
    max_requests_per_second: int = Field(5, ge=1)
    request_cache_ttl_seconds: float = Field(30, gt=0)
    request_cache_size: int = Field(512, ge=1)
    max_pending_jobs: int = Field(8, ge=1)

    @field_validator('face_model_root')
    @classmethod
    def model_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else ROOT / value

    @property
    def max_image_bytes(self) -> int:
        return int(self.max_image_size_mb * 1024 * 1024)
