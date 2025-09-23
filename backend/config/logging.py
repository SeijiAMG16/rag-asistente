import os
from logging.config import dictConfig

LOG_DIR = os.environ.get("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging():
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()" : "python_json_logger.jsonlogger.JsonFormatter",
                "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
            "plain": {
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "json",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": LOG_FILE,
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "django": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
        }
    })
