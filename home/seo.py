"""
SEO-логика сайта: title/description с fallback, canonical, hreflang,
Open Graph, robots и JSON-LD (schema.org).

Всё строится из данных CMS (страницы Wagtail + «Настройки → Site branding»),
поэтому редактор управляет SEO из админки, а шаблон base.html только выводит
результат через тег {% seo_head %}.
"""

from __future__ import annotations

import json
import re
from typing import Iterable

from django.conf import settings
from django.templatetags.static import static
from django.utils.html import strip_tags

BRAND = "Mind Technology"

# Порядок языков в hreflang и значения og:locale
LANG_ORDER = ("ru", "kk", "en")
OG_LOCALES = {"ru": "ru_RU", "kk": "kk_KZ", "en": "en_US"}
DEFAULT_LANG = "ru"

DESCRIPTION_MAX = 170


# ------------------------------------------------------------------
# URL
# ------------------------------------------------------------------

def base_url() -> str:
    """Основной адрес сайта без завершающего слеша (https://mindtech.kz)."""
    return getattr(settings, "SEO_BASE_URL", "https://mindtech.kz").rstrip("/")


def absolutize(url: str | None) -> str | None:
    if not url:
        return url
    if url.startswith(("http://", "https://")):
        return url
    if url.startswith("//"):
        return "https:" + url
    if not url.startswith("/"):
        url = "/" + url
    return base_url() + url


def page_path(page) -> str | None:
    """Относительный путь страницы с языковым префиксом (/ru/projects/)."""
    parts = page.get_url_parts()
    if not parts:
        return None
    _site_id, _root_url, path = parts
    return path


def absolute_url(page) -> str | None:
    path = page_path(page)
    return absolutize(path) if path is not None else None


def lang_of(page, request=None) -> str:
    locale = getattr(page, "locale", None)
    if locale is not None:
        return locale.language_code.lower()[:2]
    code = getattr(request, "LANGUAGE_CODE", "") or DEFAULT_LANG
    return code.lower()[:2]


# ------------------------------------------------------------------
# Индексируемость
# ------------------------------------------------------------------

def is_indexable(page, request=None) -> bool:
    if page is None:
        return False
    if request is not None and getattr(request, "is_preview", False):
        return False
    if not page.live or getattr(page, "noindex", False):
        return False
    if page.get_view_restrictions().exists():
        return False
    return True


def get_alternates(page) -> list[tuple[str, str]]:
    """
    hreflang-альтернативы: только реально опубликованные, публичные и
    индексируемые переводы. Если перевод один (только сама страница) —
    возвращаем пустой список, чтобы не выводить бессмысленную разметку.
    """
    if not is_indexable(page):
        return []

    result = {}
    for p in page.get_translations(inclusive=True).live().specific():
        if not is_indexable(p):
            continue
        url = absolute_url(p)
        if url:
            result[lang_of(p)] = url

    if len(result) < 2:
        return []

    ordered = [(lang, result[lang]) for lang in LANG_ORDER if lang in result]
    ordered += [(lang, url) for lang, url in result.items() if lang not in LANG_ORDER]
    return ordered


def x_default_url(page, alternates: list[tuple[str, str]]) -> str | None:
    """
    x-default:
    • для главных страниц — корень сайта: он сам выбирает язык
      (Django LocaleMiddleware, редирект по Accept-Language/cookie);
    • для остальных — русская версия (язык сайта по умолчанию).
    """
    if not alternates:
        return None
    if page.depth == 2:
        return base_url() + "/"
    urls = dict(alternates)
    return urls.get(DEFAULT_LANG)


# ------------------------------------------------------------------
# Title / description
# ------------------------------------------------------------------

def _clean(text: str | None) -> str:
    # теги → пробел, чтобы «<h2>Раздел</h2><p>Текст» не слипалось в «РазделТекст»
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    text = strip_tags(text)
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int = DESCRIPTION_MAX) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(",.;:—- ")
    return cut + "…"


def meta_title(page) -> str:
    if page is None:
        return BRAND
    seo_title = _clean(getattr(page, "seo_title", ""))
    if seo_title:
        return seo_title
    title = _clean(page.title)
    if "mind" in title.lower():
        return title
    return f"{title} | {BRAND}"


def default_description(branding, lang: str) -> str:
    if branding is None:
        return ""
    value = getattr(branding, f"seo_default_description_{lang}", "") or ""
    if not value.strip():
        value = getattr(branding, f"seo_default_description_{DEFAULT_LANG}", "") or ""
    return _clean(value)


def meta_description(page, branding=None, lang: str = DEFAULT_LANG) -> str:
    if page is not None:
        desc = _clean(getattr(page, "search_description", ""))
        if desc:
            return desc
        fallback = getattr(page, "get_seo_fallback_description", None)
        if callable(fallback):
            desc = _clean(fallback())
            if desc:
                return truncate(desc)
    return truncate(default_description(branding, lang))


# ------------------------------------------------------------------
# Open Graph image
# ------------------------------------------------------------------

def og_image(page, branding=None) -> dict | None:
    """
    Порядок: OG-изображение страницы → собственная картинка проекта
    (обложка hero) → изображение по умолчанию из настроек → None
    (тогда шаблон выводит статический og-cover.png, как раньше).
    """
    image = getattr(page, "og_image", None) if page is not None else None
    alt = None

    if image is None and page is not None:
        getter = getattr(page, "get_seo_image", None)
        if callable(getter):
            image = getter()

    if image is None and branding is not None:
        image = getattr(branding, "seo_default_image", None)

    if image is None:
        return None

    rendition = image.get_rendition("fill-1200x630")
    alt = image.title
    return {
        "url": absolutize(rendition.url),
        "width": rendition.width,
        "height": rendition.height,
        "alt": alt,
    }


# ------------------------------------------------------------------
# JSON-LD
# ------------------------------------------------------------------

def _phone_e164(value: str) -> str:
    digits = re.sub(r"[^\d+]", "", value or "")
    return digits


def organization_node(branding, lang: str) -> dict:
    root = base_url()
    node: dict = {
        "@type": getattr(branding, "org_schema_type", "") or "Organization",
        "@id": f"{root}/#organization",
        "name": (getattr(branding, "brand_title", "") or BRAND).strip(),
        "url": f"{root}/",
        "logo": {
            "@type": "ImageObject",
            "url": absolutize(static("img/logo-mind.png")),
            "width": 1024,
            "height": 1024,
        },
    }
    node["image"] = node["logo"]["url"]

    legal_name = (getattr(branding, "legal_name", "") or "").strip()
    if legal_name:
        node["legalName"] = legal_name

    desc = default_description(branding, lang)
    if desc:
        node["description"] = desc

    email = (getattr(branding, "email", "") or "").strip()
    phone = _phone_e164(getattr(branding, "phone_label", ""))
    if email:
        node["email"] = email
    if phone:
        node["telephone"] = phone

    street = (getattr(branding, "street_address", "") or "").strip()
    locality = (getattr(branding, "address_locality", "") or "").strip()
    if street or locality:
        address = {"@type": "PostalAddress"}
        if street:
            address["streetAddress"] = street
        if locality:
            address["addressLocality"] = locality
        region = (getattr(branding, "address_region", "") or "").strip()
        if region:
            address["addressRegion"] = region
        postal = (getattr(branding, "postal_code", "") or "").strip()
        if postal:
            address["postalCode"] = postal
        country = (getattr(branding, "address_country", "") or "").strip()
        if country:
            address["addressCountry"] = country
        node["address"] = address

    area = (getattr(branding, "area_served", "") or "").strip()
    if area:
        node["areaServed"] = {"@type": "Country", "name": area}

    if email or phone:
        contact = {"@type": "ContactPoint", "contactType": "customer service"}
        if email:
            contact["email"] = email
        if phone:
            contact["telephone"] = phone
        node["contactPoint"] = [contact]

    same_as = [
        line.strip()
        for line in (getattr(branding, "same_as", "") or "").splitlines()
        if line.strip().startswith(("http://", "https://"))
    ]
    if same_as:
        node["sameAs"] = same_as

    return node


def website_node(branding) -> dict:
    root = base_url()
    return {
        "@type": "WebSite",
        "@id": f"{root}/#website",
        "url": f"{root}/",
        "name": (getattr(branding, "brand_title", "") or BRAND).strip(),
        "inLanguage": list(LANG_ORDER),
        "publisher": {"@id": f"{root}/#organization"},
    }


def breadcrumb_items(page) -> list[tuple[str, str]]:
    """Цепочка от главной страницы локали до текущей (если глубже главной)."""
    if page.depth <= 2:
        return []
    items = []
    for ancestor in page.get_ancestors(inclusive=True).filter(depth__gte=2).specific():
        url = absolute_url(ancestor)
        if not url:
            return []
        if ancestor.depth == 2:
            name = BRAND
        else:
            getter = getattr(ancestor, "get_breadcrumb_title", None)
            name = _clean(getter() if callable(getter) else "") or _clean(ancestor.title)
        items.append((name, url))
    return items


def faq_items(page) -> list[tuple[str, str]]:
    getter = getattr(page, "get_faq_items", None)
    if not callable(getter):
        return []
    return [(_clean(q), _clean(a)) for q, a in getter() if _clean(q) and _clean(a)]


def build_json_ld(page, branding, request=None) -> str:
    lang = lang_of(page, request)
    root = base_url()
    graph: list[dict] = [organization_node(branding, lang), website_node(branding)]

    if page is not None and is_indexable(page, request):
        url = absolute_url(page)
        title = meta_title(page)
        desc = meta_description(page, branding, lang)

        page_types: list[str] = [getattr(page, "schema_page_type", "WebPage")]
        faq = faq_items(page)
        if faq:
            page_types.append("FAQPage")

        webpage: dict = {
            "@type": page_types[0] if len(page_types) == 1 else page_types,
            "@id": f"{url}#webpage",
            "url": url,
            "name": title,
            "inLanguage": lang,
            "isPartOf": {"@id": f"{root}/#website"},
        }
        if desc:
            webpage["description"] = desc
        if page.depth == 2:
            webpage["about"] = {"@id": f"{root}/#organization"}
        if page.last_published_at:
            webpage["dateModified"] = page.last_published_at.isoformat()

        image = og_image(page, branding)
        if image:
            webpage["primaryImageOfPage"] = {"@type": "ImageObject", "url": image["url"]}

        crumbs = breadcrumb_items(page)
        if crumbs:
            webpage["breadcrumb"] = {"@id": f"{url}#breadcrumb"}

        if faq:
            webpage["mainEntity"] = [
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a},
                }
                for q, a in faq
            ]

        graph.append(webpage)

        if crumbs:
            graph.append({
                "@type": "BreadcrumbList",
                "@id": f"{url}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "name": name, "item": item_url}
                    for i, (name, item_url) in enumerate(crumbs, start=1)
                ],
            })

        if getattr(page, "schema_type", "") == "service":
            service = {
                "@type": "Service",
                "@id": f"{url}#service",
                "name": _clean(getattr(page, "get_card_title", lambda: page.title)()),
                "url": url,
                "provider": {"@id": f"{root}/#organization"},
            }
            if desc:
                service["description"] = desc
            area = (getattr(branding, "area_served", "") or "").strip()
            if area:
                service["areaServed"] = {"@type": "Country", "name": area}
            graph.append(service)

    data = {"@context": "https://schema.org", "@graph": graph}
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    # защита от закрытия <script> внутри данных
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


# ------------------------------------------------------------------
# Сборка контекста для шаблона <head>
# ------------------------------------------------------------------

def head_context(page, request, branding) -> dict:
    lang = lang_of(page, request)
    indexable = is_indexable(page, request)
    alternates = get_alternates(page) if indexable else []
    canonical = absolute_url(page) if (indexable and page is not None) else None

    image = og_image(page, branding)
    other_locales: Iterable[str] = [
        OG_LOCALES[code] for code, _url in alternates if code != lang and code in OG_LOCALES
    ]

    return {
        "seo_lang": lang,
        "seo_title": meta_title(page),
        "seo_description": meta_description(page, branding, lang),
        "seo_robots": "index, follow, max-image-preview:large, max-snippet:-1" if indexable else "noindex, follow",
        "seo_canonical": canonical,
        "seo_alternates": alternates,
        "seo_x_default": x_default_url(page, alternates) if page is not None else None,
        "seo_og_url": canonical or (absolutize(request.path) if request else None),
        "seo_og_locale": OG_LOCALES.get(lang, "ru_RU"),
        "seo_og_locale_alternates": list(other_locales),
        "seo_og_image": image,
        "seo_json_ld": build_json_ld(page, branding, request),
        "seo_google_verification": (getattr(branding, "google_site_verification", "") or "").strip(),
        "seo_yandex_verification": (getattr(branding, "yandex_verification", "") or "").strip(),
        "seo_bing_verification": (getattr(branding, "bing_verification", "") or "").strip(),
    }
