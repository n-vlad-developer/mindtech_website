from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        from wagtail.signals import page_published, page_unpublished

        from home import indexnow

        page_published.connect(indexnow.page_changed, dispatch_uid="home_indexnow_published")
        page_unpublished.connect(indexnow.page_changed, dispatch_uid="home_indexnow_unpublished")
