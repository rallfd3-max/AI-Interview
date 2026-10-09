from io import BytesIO
import numpy as np
import pytest
from PIL import Image
from app.core.config import Settings
from app.core.exceptions import AppError
from app.utils.image_utils import decode_image


def test_exif_rotates_before_detection():
    image = Image.new('RGB', (40, 20), 'red')
    exif = image.getexif()
    exif[274] = 6
    stream = BytesIO()
    image.save(stream, format='JPEG', exif=exif)
    decoded = decode_image(stream.getvalue(), Settings(_env_file=None))
    assert decoded.shape == (40, 20, 3)
    assert decoded[0, 0, 2] > decoded[0, 0, 0]  # BGR for InsightFace


def test_png_gif_and_pixel_limit():
    stream = BytesIO()
    Image.new('RGB', (32, 24)).save(stream, format='PNG')
    settings = Settings(_env_file=None)
    assert decode_image(stream.getvalue(), settings).shape == (24, 32, 3)
    settings.max_image_pixels = 100
    with pytest.raises(AppError, match='pixel limit'):
        decode_image(stream.getvalue(), settings)
    stream = BytesIO()
    Image.new('RGB', (2, 2)).save(stream, format='GIF')
    with pytest.raises(AppError) as caught:
        decode_image(stream.getvalue(), settings)
    assert caught.value.code == 'INVALID_IMAGE_FORMAT'
