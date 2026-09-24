# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': "Theme Livelo",
    'version': "17.0.1.0.0",
    'category': 'Theme/Corporate',
    'summary': 'Design Theme with Theme_livelo',
    'description': 'Theme Livelo is a modern and versatile website theme'
                   ' designed for businesses looking to establish a professional presence'
                   ' and feature',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'mail', 'web_editor', 'website_blog', 'product', 'website_sale', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/amenity_data.xml',
        'data/property_data.xml',
        'views/product_views.xml',
        'views/about_us.xml',
        'views/contact_us.xml',
        'views/footer_template.xml',
        'views/header_templates.xml',
        'views/properties.xml',
        'views/pricing.xml',
        'views/shop.xml',
        'views/property_detail_page.xml',
        'views/property_listing_page.xml',
        'views/service.xml',
        'views/snippets/snippet_group.xml',
        'views/snippets/home_banner.xml',
        'views/snippets/main_banner.xml',
        'views/snippets/agents.xml',
        'views/snippets/benifits.xml',
        'views/snippets/explore_cities.xml',
        'views/snippets/freequently_questions.xml',
        'views/snippets/testimonails.xml',
        'views/snippets/property_list_snippet.xml',
        'views/snippets/latest_blog_snippet.xml',
        'views/home.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            "theme_livelo/static/src/css/style.css",
            "https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.css",
            "https://fonts.googleapis.com",
            "https://fonts.gstatic.com",
            "https://cdn.jsdelivr.net/npm/swiper@11/swiper-bundle.min.js",
            "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:ital,wght@0,100..900;1,100..900&family=Lato:ital,wght@0,100;0,300;0,400;0,700;0,900;1,100;1,300;1,400;1,700;1,900&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap",
            "theme_livelo/static/src/js/swiper.js",
            "theme_livelo/static/src/js/highlight.js",
            "theme_livelo/static/src/js/sticky_header.js",
            "theme_livelo/static/src/js/property_tab.js",
            "theme_livelo/static/src/xml/property_list_content.xml",
            "theme_livelo/static/src/js/property_category.js",
        ],
        'web.assets_backend': [
            "theme_livelo/static/src/js/welcome_message.js",
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    "license": "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
