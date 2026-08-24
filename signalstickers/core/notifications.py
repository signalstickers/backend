from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import logging

from django.conf import settings
import httpx
from pydantic import AnyUrl, BaseModel, Field

logger = logging.getLogger("main")

# Module-level pool: bounds the number of concurrent ntfy threads and reuses
# them across calls (cheaper than spawning a fresh OS thread per notification).
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="ntfy")


class NotificationPriority(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    DEFAULT = "default"
    LOW = "low"
    MIN = "min"


class Notification(BaseModel):
    topic: str
    title: str
    message: str
    tags: list[str] = Field(default_factory=list)
    priority: NotificationPriority = NotificationPriority.DEFAULT
    click_url: AnyUrl


def _send(n: Notification) -> None:
    """Sync HTTP POST. Runs on a pool thread. Must never raise."""

    # for debug
    message = n.message
    topic = n.topic
    if settings.DEBUG:
        message = f"{n.message} \n\n[Redirected for debug. Original topic: {topic}]"
        topic = "signalsticker-debug"

    url = f"{settings.NTFY_SERVER_URL.rstrip('/')}/{topic}"
    headers = {"Priority": n.priority.value, "X-Title": n.title}
    if n.tags:
        headers["Tags"] = ",".join(n.tags)
    if n.click_url:
        headers["Click"] = str(n.click_url)
    ntfy_auth_token = getattr(settings, "NTFY_AUTH_TOKEN", "")
    if ntfy_auth_token:
        headers["Authorization"] = f"Bearer {ntfy_auth_token}"

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, content=message, headers=headers)
            logger.error("notification sent")
        if not resp.is_success:
            logger.error("ntfy error %i: %s", resp.status_code, resp.text)
    except Exception as e:  # pylint: disable=broad-except
        logger.error("Error sending ntfy notification: %s", e)


def notify(
    topic: str,
    title: str,
    message: str,
    *,
    priority: NotificationPriority = NotificationPriority.DEFAULT,
    tags: list[str] | None = None,
    click_url: str | None = None,
) -> None:
    """Fire-and-forget ntfy notification.

    Returns immediately; the HTTP POST is submitted to a bounded module-level
    ThreadPoolExecutor so a slow or dead ntfy server can never block the
    calling (request) thread. Never raises. No-op when NTFY_SERVER_URL is empty.
    """
    if not getattr(settings, "NTFY_SERVER_URL", ""):
        logger.debug("ntfy not configured, skipping notification")
        return
    n = Notification(
        topic=topic,
        title=title,
        message=message,
        tags=tags or [],
        priority=priority,
        click_url=click_url,
    )
    # Resolve _send at submit time so tests can patch the module attribute.
    _executor.submit(_send, n)
