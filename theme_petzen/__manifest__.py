# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
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
    'name': 'Theme Petzen',
    'version': '17.0.1.0.0',
    'category': 'Theme/Corporate',
    'summary': 'A modern and responsive Odoo website theme designed for pet shops and services.',
    'description': 'Theme Petzen provides a complete Odoo website and eCommerce experience tailored for pet-related '
                   'businesses. Includes pre-designed templates for home, shop, services, reviews, and contact pages.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website_sale', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_category_data.xml',
        'data/petzen_review_actions.xml',
        'views/layout.xml',
        'views/components.xml',
        'views/shop.xml',
        'views/services.xml',
        'views/about.xml',
        'views/reviews.xml',
        'views/contact.xml',
        'views/cart.xml',
        'views/snippets/s_hero_snippet.xml',
        'views/snippets/s_features_snippet.xml',
        'views/snippets/s_categories_snippet.xml',
        'views/snippets/s_products_snippet.xml',
        'views/snippets/s_promo_snippet.xml',
        'views/snippets/s_gallery_snippet.xml',
        'views/snippets/s_services_snippet.xml',
        'views/home.xml',
        'views/snippets/snippets.xml',
        'views/snippets/snippet_options.xml',
        'views/petzen_review_views.xml',
        'views/product_category_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_petzen/static/src/css/reset.css',
            'theme_petzen/static/src/scss/primary_variables.scss',
            'theme_petzen/static/src/css/styles.css',
            'theme_petzen/static/src/css/pages.css',
            'theme_petzen/static/src/css/odoo.css',
            'theme_petzen/static/src/css/checkout.css',
            'theme_petzen/static/src/css/shop.css',
            'theme_petzen/static/src/css/header.css',
            'theme_petzen/static/lib/iconify/iconify-icon.min.js',
            'theme_petzen/static/src/js/petzen.js',
            'theme_petzen/static/src/js/contact.js',
            'theme_petzen/static/src/js/reviews.js',
            'theme_petzen/static/src/xml/reviews_templates.xml',
        ],
        'website.assets_wysiwyg': [
            'theme_petzen/static/src/js/snippet_options.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
