"""JSON logs; never log images, vectors or raw request bodies."""
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {'time': datetime.now(timezone.utc).isoformat(), 'level': record.levelname,
                'message': record.getMessage(), **getattr(record, 'fields', {})}
        if record.exc_info:
            data['exception'] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger('face_server')
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
