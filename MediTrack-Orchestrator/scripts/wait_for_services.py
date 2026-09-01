import os
import socket
import time
from urllib.parse import urlparse

TIMEOUT_SECONDS = int(os.getenv("WAIT_FOR_TIMEOUT_SECONDS", "180"))
URLS = [url.strip() for url in os.getenv("WAIT_FOR_URLS", "").split(",") if url.strip()]


def wait_for_tcp(url: str) -> None:
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if not host:
        raise RuntimeError(f"Cannot parse host from URL: {url}")

    deadline = time.time() + TIMEOUT_SECONDS
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"Ready: {host}:{port}")
                return
        except OSError as exc:
            last_error = exc
            print(f"Waiting for {host}:{port}...")
            time.sleep(3)

    raise TimeoutError(f"Timed out waiting for {host}:{port}: {last_error}")


for url in URLS:
    wait_for_tcp(url)