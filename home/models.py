# home/models.py

from django.db import models

from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Locale, Page, TranslatableMixin
from wagtail.snippets.models import register_snippet
from django.utils.text import slugify
from wagtail.fields import RichTextField


# =========================
# SNIPPETS: меню
# =========================

@register_snippet
class NavItem(TranslatableMixin, models.Model):
    LINK_ANCHOR = "anchor"
    LINK_URL = "url"
    LINK_CHOICES = [
        (LINK_ANCHOR, "Якорь на странице (#services)"),
        (LINK_URL, "Ссылка (/product или https://...)"),
    ]

    title = models.CharField(max_length=64)

    link_type = models.CharField(
        max_length=10,
        choices=LINK_CHOICES,
        default=LINK_ANCHOR,
    )

    # для якоря: services / process / about / contacts (без #)
    anchor = models.CharField(
        max_length=64,
        blank=True,
        help_text="ID секции на странице, например: services, process, about, contacts (без #)",
    )

    # для ссылок: /product или https://mindtech.kz/product
    url = models.CharField(
        max_length=255,
        blank=True,
        help_text="Можно относительный путь (/product) или полный URL (https://...)",
    )

    sort_order = models.PositiveIntegerField(default=0)

    panels = [
        FieldPanel("title"),
        FieldPanel("link_type"),
        FieldPanel("anchor"),
        FieldPanel("url"),
        FieldPanel("sort_order"),
    ]

    class Meta(TranslatableMixin.Meta):
        ordering = ["sort_order"]
        verbose_name = "Пункт меню"
        verbose_name_plural = "Пункты меню"

    def __str__(self):
        return self.title

    @property
    def href(self) -> str:
        if self.link_type == self.LINK_URL and self.url:
            return self.url.strip()
        if self.anchor:
            a = self.anchor.strip().lstrip("#")
            return f"#{a}"
        return "#"


# =========================
# SNIPPETS: партнёры, контакты, соцсети
# =========================

@register_snippet
class PartnerLogo(models.Model):
    name = models.CharField(max_length=80)
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    url = models.URLField(blank=True, help_text="Ссылка на сайт партнёра (необязательно)")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    panels = [
        FieldPanel("name"),
        FieldPanel("logo"),
        FieldPanel("url"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Логотип партнёра"
        verbose_name_plural = "Логотипы партнёров"

    def __str__(self):
        return self.name


@register_snippet
class ContactItem(TranslatableMixin, models.Model):
    TYPE_EMAIL = "email"
    TYPE_PHONE = "phone"
    TYPE_LINK = "link"
    TYPE_ADDRESS = "address"

    TYPE_CHOICES = [
        (TYPE_EMAIL, "Email"),
        (TYPE_PHONE, "Phone"),
        (TYPE_LINK, "Link"),
        (TYPE_ADDRESS, "Address"),
    ]

    label = models.CharField(max_length=80, help_text="Например: Email / Phone / Address")
    kind = models.CharField(max_length=16, choices=TYPE_CHOICES, default=TYPE_LINK)
    value = models.CharField(max_length=255, help_text="Текст, который показываем пользователю")
    href = models.CharField(
        max_length=255,
        blank=True,
        help_text="mailto:, tel:, https://..., или оставь пустым (для адреса можно пусто)",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    panels = [
        FieldPanel("label"),
        FieldPanel("kind"),
        FieldPanel("value"),
        FieldPanel("href"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]

    class Meta(TranslatableMixin.Meta):
        ordering = ["sort_order", "id"]
        verbose_name = "Контакт"
        verbose_name_plural = "Контакты"

    def __str__(self):
        return f"{self.label}: {self.value}"

    def get_href(self):
        if self.href:
            return self.href.strip()
        if self.kind == self.TYPE_EMAIL:
            return f"mailto:{self.value.strip()}"
        if self.kind == self.TYPE_PHONE:
            v = self.value.strip().replace(" ", "")
            return f"tel:{v}"
        return ""


@register_snippet
class SocialLink(TranslatableMixin, models.Model):
    title = models.CharField(max_length=80, help_text="Например: Instagram, Telegram")
    url = models.URLField()

    icon_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Иконка соцсети (лучше квадрат 64x64 или SVG)",
    )

    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    panels = [
        FieldPanel("title"),
        FieldPanel("url"),
        FieldPanel("icon_image"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]

    class Meta(TranslatableMixin.Meta):
        ordering = ["sort_order", "id"]
        verbose_name = "Соцсеть"
        verbose_name_plural = "Соцсети"

    def __str__(self):
        return self.title


# =========================
# SETTINGS: брендинг + астана хаб + почта формы
# =========================

@register_setting
class SiteBrandingSettings(BaseSiteSetting):
    logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # RU (по умолчанию)
    brand_title = models.CharField(max_length=80, default="Mind Technology")
    brand_subtitle = models.CharField(max_length=120, blank=True, default="IT-решения под ваш бизнес")
    footer_tagline = models.CharField(
        max_length=200,
        blank=True,
        default="Практичные IT-решения: от идеи до запуска и поддержки.",
    )

    # EN
    brand_title_en = models.CharField(max_length=80, blank=True, default="Mind Technology")
    brand_subtitle_en = models.CharField(max_length=120, blank=True, default="IT solutions for your business")
    footer_tagline_en = models.CharField(
        max_length=200,
        blank=True,
        default="Practical IT solutions: from idea to launch and support.",
    )

    # KZ
    brand_title_kk = models.CharField(
        max_length=80,
        blank=True,
        default="Mind Technology",
        verbose_name="Brand title KZ",
    )
    brand_subtitle_kk = models.CharField(
        max_length=120,
        blank=True,
        default="Бизнесіңізге арналған IT-шешімдер",
        verbose_name="Brand subtitle KZ",
    )
    footer_tagline_kk = models.CharField(
        max_length=200,
        blank=True,
        default="Практикалық IT-шешімдер: идеядан іске қосуға және қолдауға дейін.",
        verbose_name="Footer tagline KZ",
    )

    # контакты (обычно не переводят)
    email = models.EmailField(blank=True, default="info@mindtech.kz")
    phone_label = models.CharField(max_length=40, blank=True, default="+77084397098")
    phone_url = models.URLField(blank=True, default="https://wa.me/77084397098")

    # astana hub
    is_astana_hub_resident = models.BooleanField(default=True, verbose_name="Резидент Astana Hub")
    astana_hub_url = models.URLField(blank=True, default="", verbose_name="Ссылка на Astana Hub / профиль")
    astana_hub_text_ru = models.CharField(
        max_length=140,
        blank=True,
        default="Резидент Astana Hub",
        verbose_name="Текст RU (бейдж)",
    )
    astana_hub_text_en = models.CharField(
        max_length=140,
        blank=True,
        default="Astana Hub resident",
        verbose_name="Текст EN (badge)",
    )
    astana_hub_text_kk = models.CharField(
        max_length=140,
        blank=True,
        default="Astana Hub резиденті",
        verbose_name="Текст KZ (бейдж)",
    )

    astana_hub_logo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Логотип Astana Hub",
    )


    # куда отправлять форму
    contacts_email_to = models.EmailField(
        blank=True,
        default="info@mindtech.kz",
        verbose_name="Почта для заявок с сайта",
        help_text="Куда отправлять форму обратной связи",
    )

    documents_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Страница документов",
        help_text="Страница, на которую ведёт кнопка «Документы» в футере",
    )

    panels = [
        MultiFieldPanel([FieldPanel("logo")], heading="Лого"),
        MultiFieldPanel(
            [
                FieldPanel("brand_title"),
                FieldPanel("brand_subtitle"),
                FieldPanel("footer_tagline"),
            ],
            heading="Тексты RU",
        ),
        MultiFieldPanel(
            [
                FieldPanel("brand_title_en"),
                FieldPanel("brand_subtitle_en"),
                FieldPanel("footer_tagline_en"),
            ],
            heading="Тексты EN",
        ),
        MultiFieldPanel(
            [
                FieldPanel("brand_title_kk"),
                FieldPanel("brand_subtitle_kk"),
                FieldPanel("footer_tagline_kk"),
            ],
            heading="Тексты KZ",
        ),
        MultiFieldPanel(
            [
                FieldPanel("email"),
                FieldPanel("phone_label"),
                FieldPanel("phone_url"),
            ],
            heading="Контакты",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_astana_hub_resident"),
                FieldPanel("astana_hub_url"),
                FieldPanel("astana_hub_logo"),
                FieldPanel("astana_hub_text_ru"),
                FieldPanel("astana_hub_text_en"),
                FieldPanel("astana_hub_text_kk"),
            ],
            heading="Astana Hub",
        ),
        MultiFieldPanel(
            [
                FieldPanel("documents_page"),
            ],
            heading="Документы",
        ),
        MultiFieldPanel(
            [
                FieldPanel("contacts_email_to"),
            ],
            heading="Форма обратной связи",
        ),
    ]


# =========================
# BLOCKS: основной контент
# =========================

class HeroBlock(blocks.StructBlock):
    label = blocks.CharBlock(required=False)
    title = blocks.CharBlock(required=True)
    text = blocks.TextBlock(required=False)
    primary_text = blocks.CharBlock(required=False, default="Обсудить проект")
    primary_anchor = blocks.CharBlock(required=False, default="contacts")
    secondary_text = blocks.CharBlock(required=False, default="Посмотреть услуги")
    secondary_anchor = blocks.CharBlock(required=False, default="services")

    class Meta:
        label = "Hero"
        template = "blocks/hero.html"


class ServicesCardBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    text = blocks.TextBlock()

    class Meta:
        label = "Карточка услуги"


class ServicesBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="services")
    title = blocks.CharBlock(default="Услуги")
    text = blocks.TextBlock(required=False)
    cards = blocks.ListBlock(ServicesCardBlock(), min_num=1, max_num=6)

    class Meta:
        label = "Секция: Услуги"
        template = "blocks/services.html"


class StepBlock(blocks.StructBlock):
    number = blocks.CharBlock(required=True)
    title = blocks.CharBlock(required=True)
    text = blocks.TextBlock(required=False)

    class Meta:
        label = "Шаг"


class ProcessBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="process")
    title = blocks.CharBlock(default="Как мы работаем")
    text = blocks.TextBlock(required=False)
    steps = blocks.ListBlock(StepBlock(), min_num=1, max_num=8)

    class Meta:
        label = "Секция: Как мы работаем"
        template = "blocks/process.html"


class AboutBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="about")
    title = blocks.CharBlock(default="О компании")
    text = blocks.TextBlock(required=False)
    note = blocks.TextBlock(required=False)

    class Meta:
        label = "Секция: О компании"
        template = "blocks/about.html"


class ContactsBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="contacts")
    title = blocks.CharBlock(default="Контакты")
    text = blocks.TextBlock(required=False)

    email_label = blocks.CharBlock(required=False, default="Email")
    phone_label_title = blocks.CharBlock(required=False, default="Телефон")

    class Meta:
        label = "Секция: Контакты"
        template = "blocks/contacts.html"


class FooterMegaBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="contacts")

    title = blocks.CharBlock(required=False, default="О компании")
    text = blocks.TextBlock(required=False)

    bullets = blocks.ListBlock(
        blocks.CharBlock(),
        required=False,
        max_num=5,
        help_text="Короткие тезисы (до 5)",
    )

    partners_title = blocks.CharBlock(required=False, default="Нам доверяют")
    contacts_title = blocks.CharBlock(required=False, default="Контакты")
    form_title = blocks.CharBlock(required=False, default="Написать нам")

    form_name_label = blocks.CharBlock(required=False, default="Имя")
    form_contact_label = blocks.CharBlock(required=False, default="Контакт")
    form_message_label = blocks.CharBlock(required=False, default="Сообщение")

    form_name_ph = blocks.CharBlock(required=False, default="Как к вам обращаться")
    form_contact_ph = blocks.CharBlock(required=False, default="Email или телефон")
    form_message_ph = blocks.CharBlock(required=False, default="Коротко опишите задачу")

    form_submit_text = blocks.CharBlock(required=False, default="Отправить")
    form_hint = blocks.CharBlock(required=False, default="Ответим на почту или в мессенджер.")

    success_text = blocks.CharBlock(required=False, default="Спасибо! Сообщение отправлено.")
    error_text = blocks.CharBlock(required=False, default="Не удалось отправить. Попробуйте позже.")

    class Meta:
        label = "Нижний блок: компания + контакты + форма"
        template = "blocks/footer_mega.html"


# =========================
# PAGES: главная + проекты
# =========================

class HomePage(Page):
    body = StreamField(
        [
            ("hero", HeroBlock()),
            ("services", ServicesBlock()),
            ("process", ProcessBlock()),
            ("about", AboutBlock()),
            ("contacts", ContactsBlock()),
            ("footer_mega", FooterMegaBlock()),
        ],
        use_json_field=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    def get_context(self, request):
        ctx = super().get_context(request)

        qs = NavItem.objects.filter(locale=self.locale).order_by("sort_order")
        if not qs.exists():
            ru = Locale.objects.filter(language_code="ru").first()
            if ru:
                qs = NavItem.objects.filter(locale=ru).order_by("sort_order")
        ctx["nav_items"] = qs

        def by_locale(model):
            q = model.objects.filter(locale=self.locale, is_active=True).order_by("sort_order", "id")
            if q.exists():
                return q
            ru = Locale.objects.filter(language_code="ru").first()
            if ru:
                return model.objects.filter(locale=ru, is_active=True).order_by("sort_order", "id")
            return model.objects.none()

        ctx["partners_list"] = PartnerLogo.objects.filter(is_active=True).order_by("sort_order", "id")
        ctx["contacts_list"] = by_locale(ContactItem)
        ctx["socials_list"] = by_locale(SocialLink)

        return ctx


class ProjectsIndexPage(Page):
    intro_title = models.CharField(max_length=120, blank=True, default="Проекты")
    intro_text = models.TextField(
        blank=True,
        default="Подборка решений, которые мы делаем: от софта до железа и интеграций.",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("intro_title"),
                FieldPanel("intro_text"),
            ],
            heading="Вступление",
        )
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.ProjectPage"]

    template = "home/projects_index_page.html"

    def get_context(self, request):
        ctx = super().get_context(request)
        ctx["projects"] = ProjectPage.objects.child_of(self).live().order_by("-first_published_at")
        return ctx



class ProjectHeroBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    subtitle = blocks.TextBlock(required=False)

    cover = ImageChooserBlock(required=False, label="Обложка (картинка)")
    cover_alt = blocks.CharBlock(required=False, default="")

    primary_text = blocks.CharBlock(required=False, default="Запросить демо")
    primary_url = blocks.CharBlock(required=False, default="#contacts", help_text="Можно якорь #contacts или ссылка")

    secondary_text = blocks.CharBlock(required=False, default="Посмотреть возможности")
    secondary_anchor = blocks.CharBlock(required=False, default="features", help_text="ID секции (без #)")

    quick_items = blocks.ListBlock(
        blocks.CharBlock(),
        required=False,
        label="Короткие факты (плашки)",
        help_text="Например: Web + iOS, IoT, 24/7 поддержка",
        max_num=6
    )

    class Meta:
        label = "Проект: Hero"
        template = "home/blocks/project_hero.html"


class ProjectBulletBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True)

    class Meta:
        label = "Пункт"


class ProjectBulletsBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="pain")
    title = blocks.CharBlock(required=False, default="Какие боли решаем")
    subtitle = blocks.TextBlock(required=False)
    bullets = blocks.ListBlock(ProjectBulletBlock(), min_num=1, max_num=12)
    bottom_text = blocks.TextBlock(required=False,label="Текст под блоками")

    class Meta:
        label = "Проект: Список пунктов"
        template = "home/blocks/project_bullets.html"


class ProjectTwoColBulletBlock(blocks.StructBlock):
    text = blocks.CharBlock(required=True)

    class Meta:
        label = "Пункт"

class ProjectBullets2ColBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="pain")

    title = blocks.CharBlock(required=True, default="Какие боли решаем")

    subtitle = blocks.TextBlock(required=False)

    left_subtitle = blocks.CharBlock(required=True, default="В большинстве заведений гости вынуждены:")
    left_bullets = blocks.ListBlock(ProjectTwoColBulletBlock(), min_num=1, max_num=12)

    right_subtitle = blocks.CharBlock(required=True, default="Для персонала это приводит к:")
    right_bullets = blocks.ListBlock(ProjectTwoColBulletBlock(), min_num=1, max_num=12)

    bottom_text = blocks.TextBlock(required=False,label="Текст под блоками")

    class Meta:
        label = "Проект: 2 колонки (пункты)"
        template = "home/blocks/project_bullets_2col.html"

class FeatureCardBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    text = blocks.TextBlock(required=False)
    icon = ImageChooserBlock(required=False)

    class Meta:
        label = "Карточка"


class ProjectFeaturesBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="features")
    title = blocks.CharBlock(required=False, default="Из чего состоит продукт")
    subtitle = blocks.TextBlock(required=False)
    cards = blocks.ListBlock(FeatureCardBlock(), min_num=1, max_num=12)

    class Meta:
        label = "Проект: Карточки"
        template = "home/blocks/project_features.html"


class TwoColBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="overview")
    title = blocks.CharBlock(required=False, default="Как это работает")
    left_text = blocks.RichTextBlock(required=False)
    right_image = ImageChooserBlock(required=False)
    right_caption = blocks.CharBlock(required=False)
    reverse = blocks.BooleanBlock(required=False, default=False, help_text="Поменять колонки местами")

    class Meta:
        label = "Проект: 2 колонки (текст + картинка)"
        template = "home/blocks/project_two_col.html"


class RoleCardBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    text = blocks.TextBlock(required=False)
    icon = ImageChooserBlock(required=False)

    class Meta:
        label = "Роль"


class ProjectRolesBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="roles")
    title = blocks.CharBlock(required=False, default="Роли и доступы")
    subtitle = blocks.TextBlock(required=False)
    roles = blocks.ListBlock(RoleCardBlock(), min_num=1, max_num=10)
    bottom_text = blocks.TextBlock(required=False,label="Текст под блоками")

    class Meta:
        label = "Проект: Роли"
        template = "home/blocks/project_roles.html"


class StepCardBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True)
    text = blocks.TextBlock(required=False)

    class Meta:
        label = "Шаг"


class ProjectStepsBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="flow")
    title = blocks.CharBlock(required=False, default="Сценарий работы")
    subtitle = blocks.TextBlock(required=False)
    steps = blocks.ListBlock(StepCardBlock(), min_num=2, max_num=12)

    class Meta:
        label = "Проект: Шаги"
        template = "home/blocks/project_steps.html"


class ProjectGalleryBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="gallery")
    title = blocks.CharBlock(required=False, default="Скриншоты")
    images = blocks.ListBlock(ImageChooserBlock(), required=False, max_num=12)

    class Meta:
        label = "Проект: Галерея"
        template = "home/blocks/project_gallery.html"


class StatCardBlock(blocks.StructBlock):
    label = blocks.CharBlock(required=True)
    value = blocks.CharBlock(required=True)
    note = blocks.CharBlock(required=False)

    class Meta:
        label = "Цифра"


class ProjectStatsBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="stats")
    title = blocks.CharBlock(required=False, default="Цифры и эффект")
    stats = blocks.ListBlock(StatCardBlock(), required=False, max_num=8)

    class Meta:
        label = "Проект: Цифры"
        template = "home/blocks/project_stats.html"


class FAQItemBlock(blocks.StructBlock):
    q = blocks.CharBlock(required=True)
    a = blocks.TextBlock(required=True)

    class Meta:
        label = "FAQ"


class ProjectFAQBlock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="faq")
    title = blocks.CharBlock(required=False, default="FAQ")
    items = blocks.ListBlock(FAQItemBlock(), required=False, max_num=12)

    class Meta:
        label = "Проект: FAQ"
        template = "home/blocks/project_faq.html"


class ProjectCTAblock(blocks.StructBlock):
    section_id = blocks.CharBlock(required=False, default="cta")
    title = blocks.CharBlock(required=False, default="Хотите внедрить у себя?")
    text = blocks.TextBlock(required=False, default="Опишите задачу — предложим архитектуру, сроки и бюджет.")
    primary_text = blocks.CharBlock(required=False, default="Написать нам")
    primary_url = blocks.CharBlock(required=False, default="#contacts")
    secondary_url = blocks.CharBlock(required=False, default="#top")

    class Meta:
        label = "Проект: CTA"
        template = "home/blocks/project_cta.html"


class ProjectPage(Page):
    card_title = models.CharField(max_length=80, blank=True, help_text="Если пусто — заголовок страницы")
    card_description = models.TextField(max_length=240, blank=True)
    card_icon = models.ForeignKey(
        "wagtailimages.Image",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Иконка/логотип для карточки и шапки проекта"
    )

    external_url = models.URLField(blank=True, help_text="Если заполнено — кнопка поведёт туда (сайт/демо). Иначе на страницу проекта.")
    external_label = models.CharField(max_length=40, blank=True, default="Подробнее")

    body = StreamField(
        [
            ("project_hero", ProjectHeroBlock()),
            ("two_col", TwoColBlock()),
            ("bullets", ProjectBulletsBlock()),
            ("bullets_2col", ProjectBullets2ColBlock()),
            ("features", ProjectFeaturesBlock()),
            ("roles", ProjectRolesBlock()),
            ("steps", ProjectStepsBlock()),
            ("gallery", ProjectGalleryBlock()),
            ("stats", ProjectStatsBlock()),
            ("faq", ProjectFAQBlock()),
            ("cta", ProjectCTAblock()),
            ("text", blocks.RichTextBlock(required=False, label="Текст (RichText)")),
            ("image", ImageChooserBlock(label="Картинка")),
        ],
        use_json_field=True,
        blank=True,
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("card_icon"),
                FieldPanel("card_title"),
                FieldPanel("card_description"),
            ],
            heading="Карточка в списке проектов",
        ),
        MultiFieldPanel(
            [
                FieldPanel("external_url"),
                FieldPanel("external_label"),
            ],
            heading="Кнопка",
        ),
        FieldPanel("body"),
    ]

    parent_page_types = ["home.ProjectsIndexPage"]
    subpage_types = []

    template = "home/project_page.html"

    def get_card_title(self):
        return self.card_title.strip() if self.card_title else self.title

    def get_cta_url(self):
        return self.external_url.strip() if self.external_url else self.url

class DocumentsPage(Page):
    intro = models.TextField(
        blank=True,
        default="",
        verbose_name="Описание",
        help_text="Необязательный текст над списком документов",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.LegalPage"]

    max_count = 1

    template = "home/documents_page.html"

    class Meta:
        verbose_name = "Документы"


class LegalPage(Page):
    intro = models.TextField(
        blank=True,
        default="",
        verbose_name="Короткое описание (1-2 строки сверху)",
    )

    body = RichTextField(
        blank=True,
        features=["h2", "h3", "bold", "italic", "link", "ol", "ul", "hr"],
        verbose_name="Текст документа",
    )

    updated_at = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата обновления",
        help_text="Опционально. Если указать — покажем сверху",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("intro"),
                FieldPanel("updated_at"),
            ],
            heading="Вступление",
        ),
        FieldPanel("body"),
    ]

    parent_page_types = ["home.DocumentsPage"]
    subpage_types = []

    template = "home/legal_page.html"

    class Meta:
        verbose_name = "Документ"