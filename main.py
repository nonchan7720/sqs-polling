import sys
from logging import INFO, getLogger
from logging.config import dictConfig

from sqs_polling import command_main

if __name__ == "__main__":
    dictConfig(
        {
            "version": 1,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "json_ensure_ascii": False,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "json",
                },
            },
            "loggers": {
                "sqs_polling.polling": {"handlers": ["console"], "level": "INFO"}
            },
        }
    )
    logger = getLogger("sqs_polling.polling")
    logger.setLevel(INFO)
    command_main()
