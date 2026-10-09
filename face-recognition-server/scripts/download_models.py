"""Explicit first-time download. Subsequent server starts remain offline."""
import argparse
try:
    from . import _bootstrap
except ImportError:
    import _bootstrap
from app.core.config import Settings
from app.core.logging import configure_logging
from app.services.face_engine import FaceEngine


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default=None)
    args = parser.parse_args()
    settings = Settings(allow_model_download=True)
    if args.model:
        settings.face_model_name = args.model
    configure_logging()
    engine = FaceEngine(settings)
    engine.initialize()
    if not engine.ready:
        raise SystemExit('Download/model initialization failed; see log. No simulated model was installed.')
    print(f'Ready: {engine.model_name}, {engine.providers}, dimension={engine.dimension}')


if __name__ == '__main__':
    main()
