# sqs-polling
python sqs polling library

## Example

`worker/polling/task.py`

```python
import traceback
from pathlib import Path
from pprint import pprint

from sqs_polling import heartbeat, polling, ready
from sqs_polling.signal import shutdown


@polling(
    queue_name="queue_name",
    aws_profile={
        "endpoint_url": "http://localstack:4566"
    },
    max_workers=5,
    max_number_of_messages=10,
)
def task(*args, **kwargs):
    # The contents of the body of sqs are output.
    pprint({"kwargs": kwargs})


tmp_dir = get_env_value("TMPDIR")
HEARTBEAT_FILE = Path(f"{tmp_dir}/heartbeat")
READINESS_FILE = Path(f"{tmp_dir}/ready")


@heartbeat.connect
def heartbeat_sent_receiver(**_) -> None:
    update = False
    file_exists = HEARTBEAT_FILE.exists()
    try:
        # Process health checks of DBs, etc.
        if healthCheck():
            HEARTBEAT_FILE.touch()
            if file_exists:
                logger.info(f"{HEARTBEAT_FILE} updated")
            else:
                logger.info(f"{HEARTBEAT_FILE} created")
            update = True
    except Exception as e:
        logger.error("Health check failure")
        raise e
    finally:
        if not update:
            logger.error("health check failure")


@ready.connect
def worker_ready_receiver(**_) -> None:
    READINESS_FILE.touch()


@shutdown.connect
def worker_shutdown_receiver(**_) -> None:
    for file in (HEARTBEAT_FILE, READINESS_FILE):
        if file.is_file():
            file.unlink()
```

`management/commands/handler.py`

```python
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand
from sqs_polling import main


class Command(BaseCommand):
    _command_name = Path(__file__).stem

    def handle(self, *args: Any, **options: Any) -> None:
        main("worker.polling.task.task")
```
