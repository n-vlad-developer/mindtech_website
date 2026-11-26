"""
Заполняет SEO title / meta description существующих страниц рекомендованными
значениями из home/seo_recommendations.py.

По умолчанию ничего не меняет — только показывает, что будет сделано:

    python manage.py seo_fill_metadata              # просмотр (dry-run)
    python manage.py seo_fill_metadata --apply      # заполнить ТОЛЬКО пустые поля
    python manage.py seo_fill_metadata --apply --overwrite   # заменить и заполненные

Изменения сохраняются как новая ревизия Wagtail и публикуются (история
сохраняется, откат — через «История» страницы в админке). Страницы с
неопубликованными черновиками пропускаются, чтобы не опубликовать
чужие незавершённые правки.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import Truncator

from wagtail.models import Locale

from home.models import HomePage
from home.seo_recommendations import RECOMMENDATIONS

FIELDS = ("seo_title", "search_description", "schema_type")


def find_page(lang, rel_path):
    locale = Locale.objects.filter(language_code=lang).first()
    if not locale:
        return None
    home = HomePage.objects.filter(locale=locale).first()
    if not home:
        return None
    if not rel_path:
        return home.specific
    wanted = home.url_path + rel_path
    page = home.get_descendants().filter(url_path=wanted).first()
    return page.specific if page else None


class Command(BaseCommand):
    help = "Заполнить SEO-метаданные страниц рекомендованными значениями."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Сохранить и опубликовать изменения.")
        parser.add_argument("--overwrite", action="store_true", help="Заменять уже заполненные значения.")

    def handle(self, *args, apply=False, overwrite=False, **options):
        changed = skipped = missing = 0

        for (lang, rel_path), values in RECOMMENDATIONS.items():
            label = f"/{lang}/{rel_path}"
            page = find_page(lang, rel_path)
            if page is None:
                self.stdout.write(self.style.WARNING(f"[нет страницы] {label}"))
                missing += 1
                continue

            updates = {}
            for field in FIELDS:
                if field not in values or not hasattr(page, field):
                    continue
                current = getattr(page, field) or ""
                new = values[field]
                if current == new:
                    continue
                if field == "schema_type" and current not in ("", "webpage") and not overwrite:
                    continue
                if field != "schema_type" and current.strip() and not overwrite:
                    self.stdout.write(f"  = {label} {field}: оставлено «{Truncator(current).chars(70)}»")
                    continue
                updates[field] = (current, new)

            if not updates:
                continue

            if page.has_unpublished_changes:
                self.stdout.write(self.style.WARNING(f"[черновик, пропущено] {label}"))
                skipped += 1
                continue

            self.stdout.write(self.style.MIGRATE_HEADING(label))
            for field, (old, new) in updates.items():
                self.stdout.write(f"  {field}:\n    было:  {old or '—'}\n    стало: {new}")

            if apply:
                with transaction.atomic():
                    for field, (_old, new) in updates.items():
                        setattr(page, field, new)
                    revision = page.save_revision(log_action=True)
                    revision.publish()
                changed += 1

        mode = "применено" if apply else "dry-run, ничего не сохранено (добавьте --apply)"
        self.stdout.write(self.style.SUCCESS(
            f"Готово ({mode}). Изменено страниц: {changed}, пропущено с черновиками: {skipped}, не найдено: {missing}."
        ))
