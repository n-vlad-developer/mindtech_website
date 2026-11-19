from django import template
from django.utils.safestring import mark_safe

from home import seo

register = template.Library()


def _branding(context):
    from home.models import SiteBrandingSettings

    request = context.get("request")
    try:
        if request is not None:
            return SiteBrandingSettings.for_request(request)
    except Exception:
        pass
    try:
        from wagtail.models import Site

        site = Site.objects.filter(is_default_site=True).first()
        return SiteBrandingSettings.for_site(site) if site else None
    except Exception:
        return None


@register.inclusion_tag("includes/seo_head.html", takes_context=True)
def seo_head(context):
    request = context.get("request")
    page = context.get("page")
    # self — тоже страница в контексте Wagtail; берём только реальные Page
    if page is not None and not hasattr(page, "get_url_parts"):
        page = None

    branding = _branding(context)
    data = seo.head_context(page, request, branding)
    data["seo_json_ld"] = mark_safe(data["seo_json_ld"])
    data["request"] = request
    return data


@register.simple_tag(takes_context=True)
def seo_lang(context):
    page = context.get("page")
    if page is not None and hasattr(page, "locale"):
        return seo.lang_of(page)
    request = context.get("request")
    return (getattr(request, "LANGUAGE_CODE", "") or "ru")[:2]
