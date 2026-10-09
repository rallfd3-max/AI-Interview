"""Bounded image decoding, signature validation and EXIF correction."""
import base64
import binascii
import warnings
from io import BytesIO
import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from app.core.config import Settings
from app.core.exceptions import AppError
from app.schemas.recognition import FaceBox


def decode_base64(value: str, settings: Settings) -> bytes:
    if value.startswith('data:'):
        header, separator, value = value.partition(',')
        if not separator or header.lower() not in ('data:image/jpeg;base64', 'data:image/png;base64', 'data:image/jpg;base64'):
            raise AppError('INVALID_IMAGE_FORMAT', 'Only JPEG and PNG data URLs are supported.')
    if len(value) > 4 * ((settings.max_image_bytes + 2) // 3):
        raise AppError('IMAGE_TOO_LARGE', 'Image exceeds the configured byte limit.', 413)
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise AppError('INVALID_BASE64', 'Invalid Base64 encoding.') from exc
    return raw


def decode_image(raw: bytes, settings: Settings) -> np.ndarray:
    if len(raw) > settings.max_image_bytes:
        raise AppError('IMAGE_TOO_LARGE', 'Image exceeds the configured byte limit.', 413)
    if not raw:
        raise AppError('INVALID_IMAGE', 'Image is empty.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as source:
                if source.format not in ('JPEG', 'PNG'):
                    raise AppError('INVALID_IMAGE_FORMAT', 'Only JPEG and PNG images are supported.')
                if source.width * source.height > settings.max_image_pixels:
                    raise AppError('IMAGE_TOO_LARGE', 'Decoded image exceeds the pixel limit.', 413)
                image = np.array(ImageOps.exif_transpose(source).convert('RGB'))
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise AppError('IMAGE_TOO_LARGE', 'Image dimensions are too large.', 413) from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise AppError('IMAGE_DECODE_FAILED', 'Image decoding failed.') from exc


def crop_face_box(image: np.ndarray, box: FaceBox | None) -> np.ndarray:
    if box is None:
        return image
    height, width = image.shape[:2]
    if box.x + box.w > width or box.y + box.h > height:
        raise AppError('INVALID_FACE_BOX', 'face_box exceeds the EXIF-corrected image bounds.')
    return image[box.y:box.y + box.h, box.x:box.x + box.w].copy()
