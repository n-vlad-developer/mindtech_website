# home/views.py (или куда у тебя подключен обработчик формы)

from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.utils.timezone import now

from wagtail.models import Site

from .models import SiteBrandingSettings


def _is_email(value: str) -> bool:
    v = (value or "").strip()
    return "@" in v and "." in v and " " not in v and len(v) <= 254


@require_POST
def contact_submit(request):
    # honeypot от ботов
    if request.POST.get("company_hp"):
        return redirect("/#contacts?sent=1")

    name = (request.POST.get("name") or "").strip()
    contact = (request.POST.get("contact") or "").strip()
    message = (request.POST.get("message") or "").strip()

    if not name or not contact or not message:
        return redirect("/#contacts?sent=0")

    # текущий сайт Wagtail + настройки
    site = Site.find_for_request(request)
    branding = SiteBrandingSettings.for_site(site)

    # куда отправлять (из админки), fallback на EMAIL_HOST_USER
    to_email = (branding.contacts_email_to or "").strip() or getattr(settings, "EMAIL_HOST_USER", "") or "info@mindtech.kz"
    if not to_email:
        return redirect("/#contacts?sent=0")

    subject = f"Заявка с сайта: {name}"

    body = (
        f"Заявка с сайта\n"
        f"Дата: {now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"Имя: {name}\n"
        f"Контакт: {contact}\n\n"
        f"Сообщение:\n{message}\n\n"
    )

    # ВАЖНО: from_email должен быть реальным ящиком SMTP (особенно для 465/SSL)
    from_email = getattr(settings, "EMAIL_HOST_USER", None) or getattr(settings, "DEFAULT_FROM_EMAIL", None)

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=[to_email],
        headers={
            # красивое имя отправителя, если нужно
            "From": getattr(settings, "DEFAULT_FROM_EMAIL", from_email) or from_email,
        },
    )

    # reply-to только если контакт похож на email
    if _is_email(contact):
        email.reply_to = [contact]

    try:
        email.send(fail_silently=False)
        return redirect("/#contacts?sent=1")
    except Exception as e:
        # чтобы видеть причину в логах (docker logs / gunicorn)
        print("CONTACT_SUBMIT_EMAIL_ERROR:", repr(e))
        return redirect("/#contacts?sent=0")
