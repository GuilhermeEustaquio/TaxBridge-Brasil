"""Worker RQ: consome a fila `fiscal-documents` (processamento de XMLs — fase 2).

Uso: python -m app.workers.worker
"""

from redis import Redis
from rq import Queue, Worker

from app.core.config import get_settings

QUEUE_NAME = "fiscal-documents"


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.REDIS_URL)
    worker = Worker([Queue(QUEUE_NAME, connection=connection)], connection=connection)
    print(f"[worker] escutando fila '{QUEUE_NAME}' em {settings.REDIS_URL}")
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
