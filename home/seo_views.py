"""robots.txt, sitemap.xml и файл ключа IndexNow."""

from functools import reduce
from operator import or_

from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

from wagtail.contrib.sitemaps.sitemap_generator import Sitemap
from wagtail.contrib.sitemaps.views import sitemap as wagtail_sitemap_view
from wagtail.models import Page

from home import seo


# Закрытые служебные разделы. Публичные страницы, статика и медиа открыты.
ROBOTS_DISALLOW = (
    "/admin/",
    "/django-admin/",
    "/contact/submit/",
    "/search/",
    "/i18n/",
)

# Яндекс: не считать дублями страницы с UTM-метками и служебным ?sent=
ROBOTS_CLEAN_PARAM = "utm_source&utm_medium&utm_campaign&utm_content&utm_term&yclid&gclid&fbclid&sent"


def robots_txt_content() -> str:
    lines = [
        "# robots.txt - mindtech.kz",
        "# One group for all crawlers: Googlebot, Bingbot, YandexBot,",
        "# OAI-SearchBot (ChatGPT search) and others.",
        "User-agent: *",
    ]
    lines += [f"Disallow: {path}" for path in ROBOTS_DISALLOW]
    lines += [
        "Allow: /",
        f"Clean-param: {ROBOTS_CLEAN_PARAM}",
        "",
        f"Sitemap: {seo.base_url()}/sitemap.xml",
        "",
    ]
    return "\n".join(lines)


@require_GET
@cache_control(max_age=3600, public=True)
def robots_txt(request):
    return HttpResponse(robots_txt_content(), content_type="text/plain; charset=utf-8")


class LocalizedPagesSitemap(Sitemap):
    """
    Стандартный Wagtail-sitemap обходит только дерево корневой страницы
    сайта (RU). Переводы KZ/EN лежат в отдельных деревьях, поэтому берём
    деревья всех переводов корневой страницы.

    Фильтрация noindex/закрытых страниц — в SeoMixin.get_sitemap_urls.
    """

    def items(self):
        root = self.get_wagtail_site().root_page
        roots = list(root.get_translations(inclusive=True))
        condition = reduce(or_, [Q(path__startswith=r.path) for r in roots])
        return (
            Page.objects.filter(condition)
            .live()
            .public()
            .order_by("path")
            .defer_streamfields()
            .specific()
        )


SITEMAPS = {"pages": LocalizedPagesSitemap}


def sitemap_xml(request):
    response = wagtail_sitemap_view(request, sitemaps=SITEMAPS)
    response["Content-Type"] = "application/xml; charset=utf-8"
    return response


@require_GET
def indexnow_key_file(request, key):
    configured = getattr(settings, "INDEXNOW_KEY", "")
    if not configured or key != configured:
        raise Http404
    return HttpResponse(configured, content_type="text/plain; charset=utf-8")
