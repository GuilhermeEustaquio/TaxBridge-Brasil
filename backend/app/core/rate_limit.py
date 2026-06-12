import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

settings = get_settings()

_lock = threading.Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)


def auth_rate_limit(request: Request) -> None:
    """Limitador por IP para endpoints de autenticação (anti força-bruta).

    In-memory: suficiente para 1 réplica no MVP; trocar por Redis sliding-window
    ao escalar horizontalmente (fase 2).
    """
    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    now = time.monotonic()
    window = 60.0
    limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
    with _lock:
        q = _hits[ip]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                "Muitas tentativas. Aguarde um minuto e tente novamente.",
            )
        q.append(now)
