# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': "Theme Voltro",
    'version': "18.0.1.0.0",
    'category': 'Theme/Corporate',
    'summary': 'Theme Voltro is an advanced eCommerce theme crafted for '
               'digital product marketplaces. It transforms your online '
               'store into a sophisticated, technology-focused platform'
               ' with a sleek dark mode interface and modern design.',
    'description': 'Theme Voltro is an Advanced eCommerce Theme designed specifically'
                   ' for Digital Product Marketplaces. This Theme transforms your '
                   'online store into a sophisticated technology-focused platform '
                   'with its sleek dark mode interface and modern aesthetics.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'mail', 'website_sale_wishlist',
                'website_sale_comparison'],
    'data': [
        'data/website_menus.xml',
        'views/home.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/contact_us.xml',
        'views/about.xml',
        'views/shop.xml',
        'views/product_template_views.xml',
        'views/product_view_template.xml',
        'views/snippets/banner.xml',
        'views/snippets/product_categories.xml',
        'views/snippets/offer.xml',
        'views/snippets/arrivals.xml',
        'views/snippets/launches.xml',
        'views/snippets/brands.xml',
        'views/snippets/contact_us.xml',
        'views/snippets/sub_banner.xml',
        'views/snippets/services.xml',
        'views/snippets/about_story.xml',
        'views/snippets/achievements.xml',
        'views/snippets/about_team.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "/theme_voltro/static/src/js/owl.carousel.js",
            "/theme_voltro/static/src/js/owl.carousel.min.js",
            "/theme_voltro/static/src/js/product_tab.js",
            "/theme_voltro/static/src/js/product_category.js",
            "/theme_voltro/static/src/js/achievements_counter.js",
            "/theme_voltro/static/src/js/zoom_image.js",
            "theme_voltro/static/src/js/header.js",
            "/theme_voltro/static/src/js/brands.js",
            "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.0/gsap.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.0/ScrollTrigger.min.js",
            "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/EasePack.min.js",
            "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/CustomEase.min.js",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css",
            "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.theme.default.min.css",
            "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
            "https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css",
            "https://cdn.jsdelivr.net/npm/@splidejs/splide/dist/css/splide.min.css",
            "https://cdn.jsdelivr.net/npm/@splidejs/splide/dist/js/splide.min.js",
            "https://cdn.jsdelivr.net/npm/drift-zoom/dist/Drift.min.js",
            "https://cdn.jsdelivr.net/npm/drift-zoom/dist/drift-basic.min.css",
            "/theme_voltro/static/src/js/thumbnail.carousel.js",
            "/theme_voltro/static/src/js/home_banner.js",
            "/theme_voltro/static/src/css/style.css",
        ],
    },
    "images": [
        "static/description/banner.jpg",
        "static/description/theme_screenshot.jpg",
    ],
    "license": "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
