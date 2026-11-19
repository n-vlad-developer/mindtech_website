"""
Рекомендованные SEO-метаданные для существующих страниц mindtech.kz.

Ключ — (язык, путь страницы относительно главной этого языка).
Тексты опираются только на то, что уже написано на страницах сайта.
Применяются командой:  python manage.py seo_fill_metadata
"""

RECOMMENDATIONS = {
    # ------------------------------------------------------------ RU
    ("ru", ""): {
        "seo_title": "Разработка ПО и автоматизация бизнеса в Караганде | Mind Technology",
        "search_description": (
            "Mind Technology — IT-компания в Караганде. Разработка программного обеспечения, "
            "системная интеграция, автоматизация бизнеса и внедрение ИИ-решений в Казахстане."
        ),
    },
    ("ru", "projects/"): {
        "seo_title": "Проекты и решения: ИИ-агенты, интеграция, IoT | Mind Technology",
        "search_description": (
            "Проекты Mind Technology: ИИ-агенты для бизнеса, системная интеграция, платформа Q1 "
            "с умной QR-кнопкой и Smart Service Platform для сервиса в заведениях."
        ),
    },
    ("ru", "projects/system-integration/"): {
        "seo_title": "Системный интегратор в Караганде и Казахстане | Mind Technology",
        "search_description": (
            "Системная интеграция для бизнеса в Караганде и по Казахстану: связываем CRM, корпоративные "
            "сервисы, серверы, API и оборудование. Обследование, внедрение и сопровождение."
        ),
        "schema_type": "service",
    },
    ("ru", "projects/ai-agents/"): {
        "seo_title": "Разработка и внедрение ИИ-агентов для бизнеса | Mind Technology",
        "search_description": (
            "Разрабатываем ИИ-агентов для бизнеса в Казахстане: ИИ-менеджер в Telegram и на сайте, "
            "обработка документов и договоров, интеграция с CRM. Mind Technology, Караганда."
        ),
        "schema_type": "service",
    },
    ("ru", "projects/qr-кнопка/"): {
        "seo_title": "Q1 — умная QR-кнопка для заведений | Mind Technology",
        "search_description": (
            "Q1 — платформа единого QR-кода для заведений: информация и услуги для гостей, связь "
            "с персоналом, оплата и отзывы в одной точке. Разработка Mind Technology."
        ),
    },
    ("ru", "projects/1/"): {
        "seo_title": "Smart Service Platform — сервис для гостей и персонала | Mind Technology",
        "search_description": (
            "Smart Service Platform — платформа для быстрого взаимодействия клиентов и персонала: "
            "удобный сервис для гостей, контроль, аналитика и настройка процессов для сотрудников."
        ),
    },
    ("ru", "documents/"): {
        "seo_title": "Документы и правовая информация | Mind Technology",
        "search_description": (
            "Пользовательские соглашения, политики конфиденциальности и согласия на обработку "
            "персональных данных для сервисов Mind Technology."
        ),
    },
    # ------------------------------------------------------------ KK
    ("kk", ""): {
        "seo_title": "Бағдарламалық жасақтама және бизнесті автоматтандыру | Mind Technology",
        "search_description": (
            "Mind Technology — Қарағандыдағы IT-компания. Бағдарламалық жасақтама әзірлеу, жүйелік "
            "интеграция, бизнесті автоматтандыру және Қазақстанда ЖИ шешімдерін енгізу."
        ),
    },
    ("kk", "projects/"): {
        "seo_title": "Жобалар мен шешімдер | Mind Technology",
        "search_description": (
            "Mind Technology жобалары: Q1 смарт QR-түймесі және Smart Service Platform — мекемелердегі "
            "қонақтар мен қызметкерлерге арналған цифрлық сервистер."
        ),
    },
    ("kk", "projects/qr/"): {
        "seo_title": "Q1 — мекемелерге арналған смарт QR-түйме | Mind Technology",
        "search_description": (
            "Q1 — мекемелерге арналған бірыңғай QR-платформа: қонақтарға ақпарат пен қызметтер, "
            "қызметкерлермен байланыс, төлем және пікірлер бір жерде."
        ),
    },
    ("kk", "projects/1/"): {
        "seo_title": "Smart Service Platform — қонақтар мен қызметкерлерге | Mind Technology",
        "search_description": (
            "Smart Service Platform — клиенттер мен қызметкерлердің жылдам өзара әрекеттесуіне арналған "
            "платформа: қонақтарға ыңғайлы сервис, қызметкерлерге бақылау және талдау."
        ),
    },
    ("kk", "documents/"): {
        "seo_title": "Құжаттар және құқықтық ақпарат | Mind Technology",
        "search_description": (
            "Mind Technology сервистерінің пайдалану шарттары, құпиялылық саясаттары және дербес "
            "деректерді өңдеуге келісімдер."
        ),
    },
    # ------------------------------------------------------------ EN
    ("en", ""): {
        "seo_title": "Software Development & Business Automation in Kazakhstan | Mind Technology",
        "search_description": (
            "Mind Technology is an IT company in Karaganda, Kazakhstan: custom software development, "
            "system integration, business automation, IoT and AI solutions."
        ),
    },
    ("en", "projects/"): {
        "seo_title": "Projects & Solutions | Mind Technology",
        "search_description": (
            "Mind Technology projects: the Q1 smart QR button and Smart Service Platform — digital "
            "services for guests and staff in venues."
        ),
    },
    ("en", "projects/qr/"): {
        "seo_title": "Q1 Smart QR Button for Venues | Mind Technology",
        "search_description": (
            "Q1 is a single-QR platform for venues: information and services for guests, contact with "
            "staff, payments and reviews in one place. Developed by Mind Technology."
        ),
    },
    ("en", "projects/1/"): {
        "seo_title": "Smart Service Platform for Guests and Staff | Mind Technology",
        "search_description": (
            "Smart Service Platform connects customers and staff for fast service: convenient for guests, "
            "with control, analytics and process settings for employees."
        ),
    },
    ("en", "documents/"): {
        "seo_title": "Documents and Legal Information | Mind Technology",
        "search_description": (
            "Terms of use, privacy policies and personal data processing consents for Mind Technology "
            "services."
        ),
    },
}
