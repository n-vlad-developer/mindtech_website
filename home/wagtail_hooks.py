from django.urls import reverse

from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.models import Locale

from .models import DocumentsPage, NavItem


def _url_for_lang(page, lang_code: str) -> str:
    try:
        loc = Locale.objects.get(language_code=lang_code)
    except Locale.DoesNotExist:
        return page.url

    if getattr(page, "locale_id", None) == loc.id:
        return page.url

    try:
        return page.get_translation(loc).url
    except Exception:
        return page.url


@hooks.register("construct_page_context")
def add_common_context(request, context, page):
    context["nav_items"] = NavItem.objects.all()

    current = (request.LANGUAGE_CODE or "ru")[:2]

    if current == "en":
        context["current_lang"] = "en"
    elif current in ("kk", "kz"):
        context["current_lang"] = "kk"
    else:
        context["current_lang"] = "ru"

    context["lang_links"] = {
        "ru": _url_for_lang(page, "ru"),
        "en": _url_for_lang(page, "en"),
        "kk": _url_for_lang(page, "kk"),
    }


@hooks.register("construct_main_menu")
def add_documents_menu_item(request, menu_items):
    documents_page = DocumentsPage.objects.first()

    if not documents_page:
        return

    menu_items.append(
        MenuItem(
            "Документы",
            reverse(
                "wagtailadmin_explore",
                args=[documents_page.id],
            ),
            icon_name="doc-full",
            order=250,
        )
    )
