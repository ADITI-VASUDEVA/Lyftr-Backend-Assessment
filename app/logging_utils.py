import json
import logging
from datetime import datetime, timezone
from uuid import uuid4


def setup_logger(level: str) -> logging.Logger:
    logger = logging.getLogger("app")
    logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers = [handler]

    return logger


def log_request(logger: logging.Logger, payload: dict):
    logger.info(json.dumps(payload))


def new_request_id() -> str:
    return str(uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
