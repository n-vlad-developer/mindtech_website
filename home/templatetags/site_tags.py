from django import template
from django.conf import settings

from wagtail.models import Locale

from home.models import HomePage


register = template.Library()


def _lang2_from_request(request):
    return (getattr(request, "LANGUAGE_CODE", "") or "ru")[:2].lower()


def _supported_lang_codes():
    """
    Возвращает список языков из settings.LANGUAGES.

    Например:
    ["ru", "en", "kk"]
    """
    languages = getattr(
        settings,
        "LANGUAGES",
        [
            ("ru", "Русский"),
            ("en", "English"),
            ("kk", "Қазақша"),
        ],
    )

    return [
        str(code).lower()[:2]
        for code, _name in languages
    ]


def _get_home_for_lang2(lang2: str):
    """
    Возвращает опубликованную HomePage для нужной локали.
    Если не нашли — используем первую доступную HomePage.
    """
    lang2 = (lang2 or "ru").lower()[:2]

    locale = Locale.objects.filter(
        language_code=lang2
    ).first()

    if locale:
        home = (
            HomePage.objects
            .live()
            .public()
            .filter(locale=locale)
            .first()
        )

        if home:
            return home

    return (
        HomePage.objects
        .live()
        .public()
        .first()
    )


def _prefix_internal_url_with_lang(
    url: str,
    lang2: str,
) -> str:
    """
    Если в админке ввели:

        /projects/
        /about/

    превращаем в:

        /ru/projects/
        /en/projects/
        /kk/projects/

    в зависимости от текущего языка.

    Внешние ссылки, якоря и системные URL не изменяем.
    """

    if not url:
        return url

    u = url.strip()
    lang2 = (lang2 or "ru").lower()[:2]

    # ---------------------------------------------------------
    # Внешние ссылки / якоря / специальные протоколы
    # ---------------------------------------------------------

    if (
        u.startswith("#")
        or u.startswith("http://")
        or u.startswith("https://")
        or u.startswith("mailto:")
        or u.startswith("tel:")
    ):
        return u

    # ---------------------------------------------------------
    # Системные URL, которые не нужно локализовывать
    # ---------------------------------------------------------

    excluded_prefixes = (
        "/admin",
        "/django-admin",
        "/documents",
        "/search",
        "/static",
        "/media",
    )

    if u.startswith(excluded_prefixes):
        return u

    # ---------------------------------------------------------
    # Если URL уже содержит языковой префикс —
    # ничего не меняем.
    #
    # Поддерживаем языки автоматически из settings.LANGUAGES.
    # ---------------------------------------------------------

    for supported_lang in _supported_lang_codes():
        if (
            u == f"/{supported_lang}"
            or u == f"/{supported_lang}/"
            or u.startswith(f"/{supported_lang}/")
        ):
            return u

    # ---------------------------------------------------------
    # Обычный внутренний URL
    #
    # /projects/ -> /kk/projects/
    # ---------------------------------------------------------

    if u.startswith("/"):
        return f"/{lang2}{u}"

    return u


@register.simple_tag(takes_context=True)
def nav_href(context, item):
    """
    Возвращает URL пункта меню с учётом текущего языка.
    """

    request = context.get("request")
    page = context.get("page")

    lang2 = _lang2_from_request(request)

    home = _get_home_for_lang2(lang2)

    home_url = (
        home.url
        if home
        else f"/{lang2}/"
    )

    # =========================================================
    # 1. Явный URL пункта меню
    # =========================================================

    url = (
        getattr(item, "url", "")
        or ""
    ).strip()

    if url:
        return _prefix_internal_url_with_lang(
            url,
            lang2,
        )

    # =========================================================
    # 2. Anchor
    # =========================================================

    anchor = (
        getattr(item, "anchor", "")
        or ""
    ).strip()

    # Если вообще ничего не указано —
    # ведём на главную текущего языка.
    if not anchor:
        return home_url

    # ---------------------------------------------------------
    # #services
    # ---------------------------------------------------------

    if anchor.startswith("#"):
        clean_anchor = anchor.lstrip("#")

        is_home = bool(
            home
            and page
            and page.id == home.id
        )

        if is_home:
            return f"#{clean_anchor}"

        return f"{home_url}#{clean_anchor}"

    # ---------------------------------------------------------
    # Внешняя ссылка
    # ---------------------------------------------------------

    if (
        anchor.startswith("http://")
        or anchor.startswith("https://")
    ):
        return anchor

    # ---------------------------------------------------------
    # /projects/
    # ---------------------------------------------------------

    if anchor.startswith("/"):
        return _prefix_internal_url_with_lang(
            anchor,
            lang2,
        )

    # ---------------------------------------------------------
    # services
    # ---------------------------------------------------------

    is_home = bool(
        home
        and page
        and page.id == home.id
    )

    if is_home:
        return f"#{anchor}"

    return f"{home_url}#{anchor}"


@register.simple_tag(takes_context=True)
def translation_url(
    context,
    page,
    lang_code_2,
):
    """
    Возвращает URL перевода текущей страницы.

    Например:

        translation_url page "ru"
        translation_url page "en"
        translation_url page "kk"

    Если перевода страницы нет —
    отправляем на главную нужной локали.
    """

    request = context.get("request")

    want = (
        lang_code_2
        or ""
    ).lower()[:2]

    lang2 = (
        want
        or _lang2_from_request(request)
    )

    # =========================================================
    # Главная страница нужного языка
    # =========================================================

    home = _get_home_for_lang2(lang2)

    home_url = (
        home.url
        if home
        else f"/{lang2}/"
    )

    # Если page отсутствует —
    # просто идём на локализованную главную.
    if not page:
        return home_url

    # =========================================================
    # Текущая страница уже на нужном языке
    # =========================================================

    page_locale = getattr(
        page,
        "locale",
        None,
    )

    if (
        page_locale
        and page_locale.language_code.lower()[:2]
        == lang2
    ):
        return page.url

    # =========================================================
    # Ищем Locale
    # =========================================================

    locale = Locale.objects.filter(
        language_code=lang2
    ).first()

    # =========================================================
    # Основной способ Wagtail
    # =========================================================

    if locale:
        try:
            translated = page.get_translation(
                locale
            )

            if (
                translated
                and translated.live
            ):
                return translated.url

        except Exception:
            pass

    # =========================================================
    # Запасной способ
    # =========================================================

    try:
        translations = (
            page
            .get_translations(
                inclusive=False
            )
            .live()
        )

        for translated_page in translations:

            translated_locale = getattr(
                translated_page,
                "locale",
                None,
            )

            if (
                translated_locale
                and translated_locale
                .language_code
                .lower()[:2]
                == lang2
            ):
                return translated_page.url

    except Exception:
        pass

    # =========================================================
    # Перевода страницы нет — ведём на ближайший переведённый
    # раздел (например, список проектов нужного языка), а если
    # такого нет — на главную нужной локали.
    #
    # Не отправляем на "/",
    # потому что это сбросит язык на русский.
    # =========================================================

    if locale:
        try:
            for ancestor in page.get_ancestors().filter(depth__gt=2).order_by("-depth"):
                translated = ancestor.get_translation_or_none(locale)
                if translated and translated.live:
                    return translated.url
        except Exception:
            pass

    return home_url