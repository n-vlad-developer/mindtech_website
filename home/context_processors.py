from wagtail.models import Locale
from .models import NavItem


def global_nav(request):
    lang2 = (getattr(request, "LANGUAGE_CODE", "") or "ru")[:2]
    locale = Locale.objects.filter(language_code=lang2).first()
    qs = NavItem.objects.all()
    if locale:
        qs = qs.filter(locale=locale)
    return {"nav_items": qs.order_by("sort_order")}
