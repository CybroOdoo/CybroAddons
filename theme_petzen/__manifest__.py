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
    'version': '19.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'A modern and responsive website theme designed for pet shops and pet care services.',
    'description': 'Theme Petzen provides a complete website and eCommerce experience tailored for '
                   'pet-related businesses: home, shop, cart, services, about, reviews and contact pages, '
                   'dynamic "Shop by Category" and "Top Picks" snippets, quick view, service booking and '
                   'customer reviews.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['website', 'website_sale', 'website_sale_wishlist', 'crm'],
    'data': [
        'security/ir.model.access.csv',
        'data/website_menu_data.xml',
        'data/petzen_review_data.xml',
        'views/layout_templates.xml',
        'views/home_templates.xml',
        'views/shop_templates.xml',
        'views/services_templates.xml',
        'views/about_templates.xml',
        'views/reviews_templates.xml',
        'views/contact_templates.xml',
        'views/cart_templates.xml',
        'views/snippets/s_hero_snippet.xml',
        'views/snippets/s_categories_snippet.xml',
        'views/snippets/s_products_snippet.xml',
        'views/snippets/s_promo_snippet.xml',
        'views/snippets/s_gallery_snippet.xml',
        'views/snippets/s_services_snippet.xml',
        'views/snippets/snippets.xml',
        'views/petzen_review_views.xml',
        'views/product_category_views.xml',
    ],
    'demo': [
        'demo/product_category_data.xml',
    ],
    'assets': {
        # palette / fonts / buttons / header & footer templates of the design for the
        # website editor (must be in the primary variables, not in the frontend bundle)
        'web._assets_primary_variables': [
            'theme_petzen/static/src/scss/primary_variables.scss',
        ],
        'web.assets_frontend': [
            # <iconify-icon> web component with the theme icons preloaded (no external request);
            # the icons must be preloaded before the component is defined
            'theme_petzen/static/lib/iconify/petzen_icons.js',
            'theme_petzen/static/lib/iconify/iconify-icon.min.js',
            # order matters: reset.css must come before the design styles
            'theme_petzen/static/src/css/reset.css',
            'theme_petzen/static/src/css/styles.css',
            'theme_petzen/static/src/css/pages.css',
            'theme_petzen/static/src/css/odoo.css',
            'theme_petzen/static/src/css/checkout.css',
            'theme_petzen/static/src/css/shop.css',
            'theme_petzen/static/src/css/header.css',
            'theme_petzen/static/src/css/footer.css',
            'theme_petzen/static/src/js/petzen.js',
            'theme_petzen/static/src/js/products_snippet.js',
            'theme_petzen/static/src/xml/products_snippet.xml',
            'theme_petzen/static/src/js/categories_snippet.js',
            'theme_petzen/static/src/xml/categories_snippet.xml',
            'theme_petzen/static/src/js/contact.js',
            'theme_petzen/static/src/js/booking.js',
            'theme_petzen/static/src/js/reviews.js',
            'theme_petzen/static/src/xml/reviews.xml',
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
