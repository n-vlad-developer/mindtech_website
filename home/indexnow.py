"""
IndexNow: уведомление Bing, Яндекса и других участников протокола
о публикации/снятии страниц (https://www.indexnow.org/).

• Отправляется только при публикации или снятии с публикации страницы,
  а не при просмотре.
• Один и тот же URL не отправляется повторно чаще, чем раз в 10 минут.
• Запрос идёт в фоновом потоке с таймаутом — недоступность сервиса не
  замедляет и не ломает публикацию.
• Выключается переменной окружения INDEXNOW_ENABLED=False или пустым
  INDEXNOW_KEY.

Google протокол IndexNow не использует — для него работает sitemap.xml.
"""

import logging
import re
import threading
from urllib.parse import urlparse

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

KEY_RE = re.compile(r"^[A-Za-z0-9-]{8,128}$")
DEDUP_SECONDS = 600
TIMEOUT_SECONDS = 10


def is_enabled() -> bool:
    key = getattr(settings, "INDEXNOW_KEY", "")
    return bool(getattr(settings, "INDEXNOW_ENABLED", False) and key and KEY_RE.match(key))


def build_payload(urls):
    from home import seo

    base = seo.base_url()
    key = settings.INDEXNOW_KEY
    return {
        "host": urlparse(base).netloc,
        "key": key,
        "keyLocation": f"{base}/{key}.txt",
        "urlList": list(urls),
    }


def _send(payload):
    import requests

    try:
        response = requests.post(
            settings.INDEXNOW_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=TIMEOUT_SECONDS,
        )
        if response.status_code in (200, 202):
            logger.info("IndexNow: отправлено %s URL", len(payload["urlList"]))
        else:
            logger.warning("IndexNow: ответ %s — %s", response.status_code, response.text[:300])
    except Exception as exc:  # сеть, DNS, таймаут — не должны влиять на сайт
        logger.warning("IndexNow: ошибка отправки: %r", exc)


def submit_urls(urls, background=True):
    if not is_enabled():
        return []

    from home import seo

    host = urlparse(seo.base_url()).netloc
    fresh = []
    for url in dict.fromkeys(u for u in urls if u):
        if urlparse(url).netloc != host:
            continue
        if cache.add(f"indexnow:{url}", 1, DEDUP_SECONDS):
            fresh.append(url)

    if not fresh:
        return []

    payload = build_payload(fresh)
    if background:
        threading.Thread(target=_send, args=(payload,), daemon=True).start()
    else:
        _send(payload)
    return fresh


def page_changed(sender, instance, **kwargs):
    """Обработчик сигналов page_published / page_unpublished."""
    if not is_enabled():
        return
    from home import seo

    page = instance.specific
    url = seo.absolute_url(page)
    if url:
        # и опубликованная, и снятая/скрытая страница: поисковик перепроверит URL
        submit_urls([url])
