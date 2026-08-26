import json
import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.config.config import get_settings

logger = logging.getLogger("gg_imports.http")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps({"timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                           "level": record.levelname, "logger": record.name,
                           "message": record.getMessage()}, ensure_ascii=False)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(get_settings().LOG_LEVEL.upper())


class ProductionMiddleware(BaseHTTPMiddleware):
    _requests: dict[str, deque[float]] = defaultdict(deque)
    _lock = Lock()

    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        if self._check_rate_limit(request):
            response = JSONResponse({"detail": "Muitas tentativas. Aguarde e tente novamente."}, 429,
                                    headers={"Retry-After": "60"})
        else:
            try:
                response = await call_next(request)
            except Exception:
                logger.exception("unhandled_request_error request_id=%s path=%s", request_id, request.url.path)
                response = JSONResponse({"detail": "Serviço temporariamente indisponível",
                                         "request_id": request_id}, status_code=503)
        response.headers.update({"X-Request-ID": request_id, "X-Content-Type-Options": "nosniff",
                                 "X-Frame-Options": "DENY", "Referrer-Policy": "strict-origin-when-cross-origin",
                                 "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                                 "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'"})
        if get_settings().ENVIRONMENT.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        logger.info("request request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
                    request_id, request.method, request.url.path, response.status_code,
                    (time.perf_counter() - started) * 1000)
        return response

    def _check_rate_limit(self, request: Request) -> bool:
        settings = get_settings()
        if not settings.RATE_LIMIT_ENABLED or request.method != "POST":
            return False
        limit = {"/auth/login": settings.RATE_LIMIT_LOGIN, "/clients/": settings.RATE_LIMIT_REGISTER,
                 "/orders/track": settings.RATE_LIMIT_TRACK_ORDER}.get(request.url.path)
        if not limit:
            return False
        forwarded = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        client_ip = forwarded or (request.client.host if request.client else "unknown")
        key, now = f"{client_ip}:{request.url.path}", time.monotonic()
        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= limit:
                return True
            bucket.append(now)
        return False
