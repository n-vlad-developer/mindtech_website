"""
Тесты SEO: robots.txt, sitemap.xml, title/description, canonical, hreflang,
JSON-LD, заголовки, переключатель языков, IndexNow и команда seo_fill_metadata.

Запуск:  python manage.py test home
"""

import json
import re
import xml.etree.ElementTree as ET
from io import StringIO
from unittest import mock
from urllib.parse import quote

from bs4 import BeautifulSoup
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings

from wagtail.models import Locale, Page, PageViewRestriction, Site

from home import indexnow
from home.models import (
    DocumentsPage,
    HomePage,
    LegalPage,
    ProjectPage,
    ProjectsIndexPage,
)

BASE = "https://mindtech.kz"
SM_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9", "xhtml": "http://www.w3.org/1999/xhtml"}


def publish(page):
    page.save_revision().publish()
    page.refresh_from_db()
    return page


def translate(page, locale):
    copy = page.copy_for_translation(locale)
    return publish(copy.specific)


class SeoSiteMixin:
    """Небольшое дерево страниц, повторяющее структуру mindtech.kz."""

    @classmethod
    def setUpTestData(cls):
        cls.ru = Locale.objects.get(language_code="ru")
        cls.kk, _ = Locale.objects.get_or_create(language_code="kk")
        cls.en, _ = Locale.objects.get_or_create(language_code="en")

        root = Page.get_first_root_node()
        cls.home = root.add_child(instance=HomePage(
            title="Mind Tech - IT-решения",
            slug="home-ru",
            seo_title="Разработка ПО и автоматизация бизнеса в Караганде | Mind Technology",
            search_description="Mind Technology — IT-компания в Караганде.",
            body=[("hero", {"title": "Разрабатываем цифровые и аппаратные решения для бизнеса", "text": "Текст"})],
        ))
        site = Site.objects.get(is_default_site=True)
        old_root = site.root_page
        site.root_page = cls.home
        site.save()
        if old_root.id != cls.home.id and old_root.depth == 2:
            old_root.delete()

        cls.projects = cls.home.add_child(instance=ProjectsIndexPage(
            title="Mind Tech - Проекты", slug="projects", intro_title="Проекты",
            intro_text="Подборка решений, которые мы делаем.",
        ))
        cls.si = cls.projects.add_child(instance=ProjectPage(
            title="Системная интеграция",
            slug="system-integration",
            card_description="Объединяем программные сервисы, серверы и оборудование в единую систему.",
            schema_type="service",
            body=[
                ("project_hero", {"title": "Системная интеграция в Казахстане", "subtitle": "Подзаголовок"}),
                ("faq", {"title": "Вопросы", "items": [
                    {"q": "От чего зависят стоимость и сроки?", "a": "От количества систем."},
                ]}),
            ],
        ))
        cls.qr = cls.projects.add_child(instance=ProjectPage(
            title="Q1 - УМНАЯ QR КНОПКА", slug="qr-кнопка",
            card_description="Платформа единого QR для заведений.",
        ))
        cls.hidden = cls.projects.add_child(instance=ProjectPage(
            title="Скрытый проект", slug="hidden", noindex=True,
        ))
        cls.draft = cls.projects.add_child(instance=ProjectPage(
            title="Черновик", slug="draft", live=False,
        ))
        cls.private = cls.projects.add_child(instance=ProjectPage(title="Закрытый", slug="private"))
        PageViewRestriction.objects.create(page=cls.private, restriction_type="password", password="x")

        cls.docs = cls.home.add_child(instance=DocumentsPage(title="Документы", slug="documents"))
        cls.legal = cls.docs.add_child(instance=LegalPage(
            title="Политика конфиденциальности", slug="privacy_policy",
            intro="Как мы обрабатываем данные пользователей приложения.",
        ))

        for page in (cls.home, cls.projects, cls.si, cls.qr, cls.hidden, cls.private, cls.docs, cls.legal):
            publish(page)

        # Переводы: главная, проекты, Q1 и документы — как на живом сайте
        cls.home_kk = translate(cls.home, cls.kk)
        cls.home_en = translate(cls.home, cls.en)
        # переведённые названия (на живом сайте переводы сделаны вручную)
        HomePage.objects.filter(pk=cls.home_kk.pk).update(title="Mind Tech – IT шешімдері", seo_title="", search_description="")
        HomePage.objects.filter(pk=cls.home_en.pk).update(title="Mind Tech - IT solutions", seo_title="", search_description="")
        cls.projects_kk = translate(cls.projects, cls.kk)
        cls.projects_en = translate(cls.projects, cls.en)
        cls.qr_kk = translate(cls.qr, cls.kk)
        cls.qr_en = translate(cls.qr, cls.en)

    def setUp(self):
        cache.clear()

    def soup(self, url, **extra):
        response = self.client.get(url, **extra)
        self.assertEqual(response.status_code, 200, url)
        return BeautifulSoup(response.content.decode("utf-8"), "html.parser")

    def json_ld(self, soup):
        scripts = soup.select('script[type="application/ld+json"]')
        self.assertEqual(len(scripts), 1)
        return json.loads(scripts[0].string)

    def graph_types(self, data):
        types = []
        for node in data["@graph"]:
            t = node["@type"]
            types += t if isinstance(t, list) else [t]
        return types


class RobotsTxtTests(SeoSiteMixin, TestCase):
    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("text/plain"))
        body = response.content.decode()
        self.assertIn("User-agent: *", body)
        self.assertIn(f"Sitemap: {BASE}/sitemap.xml", body)
        for path in ("/admin/", "/django-admin/", "/search/", "/contact/submit/"):
            self.assertIn(f"Disallow: {path}", body)
        # нет глобального запрета и запрета для поисковых роботов
        self.assertNotRegex(body, r"(?m)^Disallow:\s*/\s*$")
        self.assertNotIn("OAI-SearchBot\nDisallow", body)
        for public in ("/static/", "/media/", "/ru/", "/kk/", "/en/"):
            self.assertNotIn(f"Disallow: {public}", body)


class SitemapTests(SeoSiteMixin, TestCase):
    def get_urls(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertIn("xml", response["Content-Type"])
        tree = ET.fromstring(response.content)
        return tree, [loc.text for loc in tree.findall("sm:url/sm:loc", SM_NS)]

    def test_contains_all_languages_and_public_pages(self):
        _tree, urls = self.get_urls()
        for path in ("/ru/", "/kk/", "/en/", "/ru/projects/", "/kk/projects/", "/en/projects/",
                     "/ru/projects/system-integration/", "/kk/projects/qr-кнопка/",
                     "/ru/documents/", "/ru/documents/privacy_policy/"):
            self.assertIn(BASE + quote(path), urls, path)

    def test_excludes_hidden_draft_private(self):
        _tree, urls = self.get_urls()
        joined = "\n".join(urls)
        self.assertNotIn("/hidden/", joined)
        self.assertNotIn("/draft/", joined)
        self.assertNotIn("/private/", joined)

    def test_absolute_https_unique_with_real_lastmod(self):
        tree, urls = self.get_urls()
        self.assertEqual(len(urls), len(set(urls)))
        self.assertTrue(all(u.startswith(BASE + "/") for u in urls))
        lastmods = [el.text for el in tree.findall("sm:url/sm:lastmod", SM_NS)]
        self.assertEqual(len(lastmods), len(urls))
        self.home.refresh_from_db()
        self.assertIn(self.home.last_published_at.strftime("%Y-%m-%d"), lastmods)

    def test_hreflang_alternates_in_sitemap(self):
        tree, _urls = self.get_urls()
        for url in tree.findall("sm:url", SM_NS):
            if url.find("sm:loc", SM_NS).text == BASE + "/ru/":
                langs = {l.get("hreflang") for l in url.findall("xhtml:link", SM_NS)}
                self.assertEqual(langs, {"ru", "kk", "en"})
                break
        else:
            self.fail("главная RU не найдена в sitemap")


class HeadTagsTests(SeoSiteMixin, TestCase):
    def test_home_ru(self):
        s = self.soup("/ru/")
        self.assertEqual(s.html["lang"], "ru")
        self.assertEqual(s.title.string, "Разработка ПО и автоматизация бизнеса в Караганде | Mind Technology")
        self.assertEqual(s.find("meta", attrs={"name": "description"})["content"], "Mind Technology — IT-компания в Караганде.")
        self.assertEqual(s.find("link", rel="canonical")["href"], BASE + "/ru/")
        self.assertIn("index", s.find("meta", attrs={"name": "robots"})["content"])
        self.assertNotIn("noindex", s.find("meta", attrs={"name": "robots"})["content"])
        alts = {l["hreflang"]: l["href"] for l in s.select('link[rel="alternate"][hreflang]')}
        self.assertEqual(alts, {"ru": BASE + "/ru/", "kk": BASE + "/kk/", "en": BASE + "/en/", "x-default": BASE + "/"})
        self.assertEqual(s.find("meta", property="og:url")["content"], BASE + "/ru/")
        self.assertEqual(len(s.find_all("title")), 1)
        self.assertEqual(len(s.find_all("link", rel="canonical")), 1)

    def test_kk_and_en_have_own_canonical_lang_and_description(self):
        for lang, word in (("kk", "Қарағанды"), ("en", "Karaganda")):
            s = self.soup(f"/{lang}/")
            self.assertEqual(s.html["lang"], lang)
            self.assertEqual(s.find("link", rel="canonical")["href"], f"{BASE}/{lang}/")
            desc = s.find("meta", attrs={"name": "description"})["content"]
            self.assertIn(word, desc)
            self.assertNotIn("Караганд", desc)  # не русский текст на чужом языке
            self.assertEqual(s.find("meta", property="og:locale")["content"], {"kk": "kk_KZ", "en": "en_US"}[lang])

    def test_canonical_ignores_query_string(self):
        s = self.soup("/ru/?utm_source=test&sent=1")
        self.assertEqual(s.find("link", rel="canonical")["href"], BASE + "/ru/")

    def test_fallback_title_and_description(self):
        s = self.soup("/ru/projects/qr-кнопка/")
        self.assertEqual(s.title.string, "Q1 - УМНАЯ QR КНОПКА | Mind Technology")
        self.assertEqual(s.find("meta", attrs={"name": "description"})["content"], "Платформа единого QR для заведений.")
        s = self.soup("/ru/documents/privacy_policy/")
        self.assertIn("обрабатываем данные", s.find("meta", attrs={"name": "description"})["content"])

    def test_titles_unique(self):
        titles = [self.soup(u).title.string for u in (
            "/ru/", "/kk/", "/en/", "/ru/projects/", "/ru/projects/system-integration/",
            "/ru/projects/qr-кнопка/", "/ru/documents/", "/ru/documents/privacy_policy/",
        )]
        self.assertEqual(len(titles), len(set(titles)), titles)

    def test_page_without_translations_has_no_hreflang(self):
        s = self.soup("/ru/projects/system-integration/")
        self.assertEqual(s.select('link[rel="alternate"][hreflang]'), [])
        self.assertEqual(s.find("link", rel="canonical")["href"], BASE + "/ru/projects/system-integration/")

    def test_partial_translations_hreflang(self):
        s = self.soup("/kk/projects/qr-кнопка/")
        alts = {l["hreflang"]: l["href"] for l in s.select('link[rel="alternate"][hreflang]')}
        self.assertEqual(set(alts), {"ru", "kk", "en", "x-default"})
        self.assertEqual(alts["x-default"], alts["ru"])
        self.assertEqual(s.find("link", rel="canonical")["href"], alts["kk"])

    def test_noindex_page(self):
        s = self.soup("/ru/projects/hidden/")
        self.assertIn("noindex", s.find("meta", attrs={"name": "robots"})["content"])
        self.assertIsNone(s.find("link", rel="canonical"))

    def test_search_page_noindex(self):
        response = self.client.get("/search/?query=x")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'content="noindex, follow"', response.content)

    def test_verification_meta_from_settings(self):
        from home.models import SiteBrandingSettings

        branding = SiteBrandingSettings.for_site(Site.objects.get(is_default_site=True))
        branding.google_site_verification = "google-token-123"
        branding.yandex_verification = "yandex-token-456"
        branding.bing_verification = "bing-token-789"
        branding.save()
        s = self.soup("/ru/")
        self.assertEqual(s.find("meta", attrs={"name": "google-site-verification"})["content"], "google-token-123")
        self.assertEqual(s.find("meta", attrs={"name": "yandex-verification"})["content"], "yandex-token-456")
        self.assertEqual(s.find("meta", attrs={"name": "msvalidate.01"})["content"], "bing-token-789")

    def test_no_verification_meta_by_default(self):
        s = self.soup("/ru/")
        self.assertIsNone(s.find("meta", attrs={"name": "google-site-verification"}))


class StructuredDataTests(SeoSiteMixin, TestCase):
    def test_home_organization_website(self):
        data = self.json_ld(self.soup("/ru/"))
        self.assertEqual(data["@context"], "https://schema.org")
        org = next(n for n in data["@graph"] if n["@id"] == BASE + "/#organization")
        self.assertEqual(org["name"], "Mind Technology")
        self.assertEqual(org["address"]["addressLocality"], "Караганда")
        self.assertEqual(org["address"]["streetAddress"], "ул. Жамбыла, 42")
        self.assertEqual(org["address"]["addressCountry"], "KZ")
        self.assertEqual(org["email"], "info@mindtech.kz")
        self.assertEqual(org["telephone"], "+77084397098")
        self.assertTrue(org["logo"]["url"].startswith(BASE))
        types = self.graph_types(data)
        self.assertIn("WebSite", types)
        self.assertIn("WebPage", types)
        for forbidden in ("AggregateRating", "Review", "Article"):
            self.assertNotIn(forbidden, json.dumps(data))

    def test_service_page(self):
        data = self.json_ld(self.soup("/ru/projects/system-integration/"))
        types = self.graph_types(data)
        self.assertIn("Service", types)
        self.assertIn("BreadcrumbList", types)
        self.assertIn("FAQPage", types)
        service = next(n for n in data["@graph"] if n["@type"] == "Service")
        self.assertEqual(service["provider"]["@id"], BASE + "/#organization")
        crumbs = next(n for n in data["@graph"] if n["@type"] == "BreadcrumbList")["itemListElement"]
        self.assertEqual([c["name"] for c in crumbs], ["Mind Technology", "Проекты", "Системная интеграция"])
        self.assertEqual([c["item"] for c in crumbs], [
            BASE + "/ru/", BASE + "/ru/projects/", BASE + "/ru/projects/system-integration/",
        ])
        webpage = next(n for n in data["@graph"] if "FAQPage" in (n["@type"] if isinstance(n["@type"], list) else [n["@type"]]))
        self.assertEqual(webpage["mainEntity"][0]["name"], "От чего зависят стоимость и сроки?")

    def test_product_page_is_not_service(self):
        data = self.json_ld(self.soup("/ru/projects/qr-кнопка/"))
        self.assertNotIn("Service", self.graph_types(data))

    def test_projects_index_collection_page(self):
        data = self.json_ld(self.soup("/ru/projects/"))
        self.assertIn("CollectionPage", self.graph_types(data))

    def test_json_ld_escapes_html(self):
        ProjectPage.objects.filter(pk=self.qr.pk).update(search_description="</script><b>x</b> & y")
        html = self.client.get("/ru/projects/qr-кнопка/").content.decode()
        block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1)
        self.assertNotIn("</script", block)
        json.loads(block)


class HeadingsAndLinksTests(SeoSiteMixin, TestCase):
    def test_single_h1_on_main_pages(self):
        for url in ("/ru/", "/ru/projects/", "/ru/projects/system-integration/",
                    "/ru/projects/qr-кнопка/", "/ru/documents/", "/ru/documents/privacy_policy/"):
            h1 = self.soup(url).find_all("h1")
            self.assertEqual(len(h1), 1, f"{url}: {h1}")

    def test_project_h1_is_hero_title(self):
        s = self.soup("/ru/projects/system-integration/")
        self.assertEqual(s.h1.get_text(strip=True), "Системная интеграция в Казахстане")
        self.assertIn("phero-title", s.h1["class"])

    def test_project_without_hero_uses_page_title(self):
        s = self.soup("/ru/projects/qr-кнопка/")
        self.assertEqual(s.h1.get_text(strip=True), "Q1 - УМНАЯ QR КНОПКА")

    def test_projects_index_links_are_plain_hrefs(self):
        s = self.soup("/ru/projects/")
        hrefs = {a["href"] for a in s.find_all("a", href=True)}
        self.assertIn("/ru/projects/system-integration/", hrefs)

    def test_language_switch_without_translation_goes_to_section(self):
        s = self.soup("/ru/projects/system-integration/")
        switch = {a.get_text(strip=True): a["href"] for a in s.select("#langSwitch a")}
        self.assertEqual(switch["KZ"], "/kk/projects/")
        self.assertEqual(switch["EN"], "/en/projects/")

    def test_language_switch_with_translation(self):
        s = self.soup("/ru/projects/qr-кнопка/")
        switch = {a.get_text(strip=True): a["href"] for a in s.select("#langSwitch a")}
        self.assertEqual(switch["KZ"], self.qr_kk.url)
        for href in switch.values():
            self.assertEqual(self.client.get(href).status_code, 200, href)


class RegressionTests(SeoSiteMixin, TestCase):
    def test_root_redirects_to_language(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/ru/")
        self.assertIn("Accept-Language", response["Vary"])

    def test_admin_login_available(self):
        self.assertIn(self.client.get("/admin/").status_code, (200, 302))
        self.assertEqual(self.client.get("/admin/login/").status_code, 200)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_contact_form_still_works(self):
        response = self.client.post("/contact/submit/", {"name": "Тест", "contact": "a@b.kz", "message": "Привет"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("sent=1", response["Location"])
        self.assertEqual(len(mail.outbox), 1)

    def test_admin_editors_render_with_seo_fields(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_superuser("admin-test", "a@example.com", "pass-for-tests-only")
        self.client.force_login(user)
        for page in (self.home, self.projects, self.si, self.docs, self.legal):
            response = self.client.get(f"/admin/pages/{page.id}/edit/")
            self.assertEqual(response.status_code, 200, page)
            self.assertContains(response, "noindex")
            self.assertContains(response, "og_image")
        self.assertContains(self.client.get(f"/admin/pages/{self.si.id}/edit/"), "schema_type")
        site = Site.objects.get(is_default_site=True)
        response = self.client.get(f"/admin/settings/home/sitebrandingsettings/{site.id}/")
        self.assertEqual(response.status_code, 200)
        for field in ("google_site_verification", "yandex_verification", "bing_verification", "street_address"):
            self.assertContains(response, field)
        # предпросмотр страницы не индексируется
        response = self.client.get(f"/admin/pages/{self.si.id}/edit/preview/")
        self.assertIn(response.status_code, (200, 405))

    def test_all_public_pages_200(self):
        for page in Page.objects.live().filter(depth__gte=2).specific():
            if page.get_view_restrictions().exists():
                continue
            self.assertEqual(self.client.get(page.url).status_code, 200, page.url)


class IndexNowTests(SeoSiteMixin, TestCase):
    def test_disabled_by_default(self):
        with mock.patch("requests.post") as post:
            publish(self.qr)
        post.assert_not_called()
        self.assertEqual(self.client.get("/abcdefgh12345678.txt").status_code, 404)

    @override_settings(INDEXNOW_ENABLED=True, INDEXNOW_KEY="abcdefgh12345678")
    def test_submit_on_publish_with_dedup(self):
        with mock.patch("home.indexnow.threading.Thread") as thread:
            publish(self.qr)
            publish(self.qr)  # повтор в пределах 10 минут не отправляется
        self.assertEqual(thread.call_count, 1)
        payload = thread.call_args.kwargs["args"][0]
        self.assertEqual(payload["host"], "mindtech.kz")
        self.assertEqual(payload["keyLocation"], BASE + "/abcdefgh12345678.txt")
        self.assertEqual(payload["urlList"], [BASE + quote("/ru/projects/qr-кнопка/")])

    @override_settings(INDEXNOW_ENABLED=True, INDEXNOW_KEY="abcdefgh12345678")
    def test_key_file(self):
        response = self.client.get("/abcdefgh12345678.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "abcdefgh12345678")
        self.assertEqual(self.client.get("/zzzzzzzz00000000.txt").status_code, 404)

    @override_settings(INDEXNOW_ENABLED=True, INDEXNOW_KEY="abcdefgh12345678")
    def test_network_error_is_swallowed(self):
        with mock.patch("requests.post", side_effect=OSError("down")):
            indexnow.submit_urls([BASE + "/ru/"], background=False)  # не бросает исключение

    @override_settings(INDEXNOW_ENABLED=True, INDEXNOW_KEY="abcdefgh12345678")
    def test_foreign_host_not_submitted(self):
        self.assertEqual(indexnow.submit_urls(["https://example.com/x/"], background=False), [])


class FillMetadataCommandTests(SeoSiteMixin, TestCase):
    def run_cmd(self, *args):
        out = StringIO()
        call_command("seo_fill_metadata", *args, stdout=out)
        return out.getvalue()

    def test_dry_run_changes_nothing(self):
        self.run_cmd()
        self.qr.refresh_from_db()
        self.assertEqual(self.qr.seo_title, "")

    def test_apply_fills_only_empty_and_keeps_history(self):
        revisions_before = self.qr.revisions.count()
        self.run_cmd("--apply")
        self.qr.refresh_from_db()
        self.assertEqual(self.qr.seo_title, "Q1 — умная QR-кнопка для заведений | Mind Technology")
        self.assertEqual(self.qr.revisions.count(), revisions_before + 1)
        # уже заполненное не трогаем без --overwrite
        self.home.refresh_from_db()
        self.assertEqual(self.home.search_description, "Mind Technology — IT-компания в Караганде.")
        # kk-перевод получил свои тексты
        self.home_kk.refresh_from_db()
        self.assertIn("Қарағанды", self.home_kk.search_description)

    def test_skips_pages_with_drafts(self):
        self.qr.title = "Новый черновик"
        self.qr.save_revision()
        output = self.run_cmd("--apply")
        self.qr.refresh_from_db()
        self.assertEqual(self.qr.seo_title, "")
        self.assertIn("qr-кнопка", output)
