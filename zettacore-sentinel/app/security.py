"""Small ASGI security helpers for ZettaCore Sentinel.

The request limiter is deliberately best-effort and process-local. Use a shared
store for production across multiple workers/instances.
"""
from __future__ import annotations

import ipaddress
import os
import time
from collections import OrderedDict, deque

from starlette.responses import JSONResponse


class BodySizeLimitMiddleware:
    """Cap declared and streamed HTTP request bodies, including chunked bodies."""

    def __init__(self, app, max_bytes: int = 12288) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name == b"content-length":
                try:
                    declared = int(value)
                except ValueError:
                    await self._reject(send, 400, "Cabecera Content-Length no válida.")
                    return
                if declared < 0:
                    await self._reject(send, 400, "Cabecera Content-Length no válida.")
                    return
                if declared > self.max_bytes:
                    await self._reject(send, 413, "La petición supera el tamaño máximo permitido.")
                    return
                break

        received = 0
        response_started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _PayloadTooLarge
            return message

        async def tracking_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _PayloadTooLarge:
            if not response_started:
                await self._reject(send, 413, "La petición supera el tamaño máximo permitido.")

    @staticmethod
    async def _reject(send, status_code: int, detail: str) -> None:
        response = JSONResponse({"detail": detail}, status_code=status_code)
        async def no_receive():
            return {"type": "http.request", "body": b"", "more_body": False}
        await response({"type": "http"}, no_receive, send)


class _PayloadTooLarge(Exception):
    pass


class SlidingWindowLimiter:
    """Bounded per-process sliding-window limiter; not distributed."""

    def __init__(self, window_seconds=60, max_requests=30, max_external=5, max_clients=5000):
        self.window_seconds = float(window_seconds)
        self.max_requests = int(max_requests)
        self.max_external = int(max_external)
        self.max_clients = max(1, int(max_clients))
        self.events: OrderedDict[str, deque] = OrderedDict()

    def reset(self):
        self.events.clear()

    def _prune(self, bucket, now):
        while bucket and now - bucket[0][0] >= self.window_seconds:
            bucket.popleft()

    def allow(self, client, external=False, now=None):
        now = time.monotonic() if now is None else now
        # Prune expired buckets before adding a new client; this keeps memory bounded.
        for key in list(self.events):
            self._prune(self.events[key], now)
            if not self.events[key]:
                del self.events[key]

        if client not in self.events and len(self.events) >= self.max_clients:
            # Hard cap: evict the least recently used bucket rather than growing forever.
            self.events.popitem(last=False)

        bucket = self.events.setdefault(client, deque())
        self.events.move_to_end(client)
        external_count = sum(1 for _, is_external in bucket if is_external)
        if len(bucket) >= self.max_requests or (external and external_count >= self.max_external):
            return False
        bucket.append((now, bool(external)))
        return True


def trusted_proxy_hops() -> int:
    """Explicitly configured trusted proxy count; defaults to no forwarded-header trust."""
    try:
        return max(0, min(5, int(os.getenv("TRUSTED_PROXY_HOPS", "0"))))
    except (TypeError, ValueError):
        return 0


def client_ip(scope, trusted_hops=0):
    """Use the direct peer unless the operator explicitly configures trusted proxies."""
    client = scope.get("client")
    direct = client[0] if client else "unknown"
    if trusted_hops <= 0:
        return direct
    values = [
        value.decode("latin-1")
        for name, value in scope.get("headers", [])
        if name == b"x-forwarded-for"
    ]
    entries = [part.strip() for value in values for part in value.split(",") if part.strip()]
    if len(entries) < trusted_hops:
        return direct
    candidate = entries[-trusted_hops]
    try:
        return ipaddress.ip_address(candidate).compressed
    except ValueError:
        return direct
