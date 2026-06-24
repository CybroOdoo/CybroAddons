# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
    'name': 'Theme Restaurant',
    'version': '19.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Dark gold restaurant-inspired eCommerce theme with rich '
               'snippets and editorial design',
    'description': """
        Theme Restaurant Savora
        ============
        A premium dark restaurant-inspired eCommerce theme for Odoo 19.
        Combines fire-led dining aesthetics — deep charcoal, warm gold accents,
        Playfair Display serif typography — with a fully-featured eCommerce
        storefront including shop, product pages, cart, and checkout.
        Key Features:
        - Dark charcoal + gold color palette
        - Playfair Display (headings) + Inter (body) typography
        - 8 drag-and-drop Website Builder snippets
        - Hero, Story, Menu Tabs, Gallery, Reviews, Reservation CTA sections
        - Custom shop with sidebar filters
        - Cart sidebar drawer
        - Fully responsive mobile layout
            """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_sale', 'website_sale_wishlist', 'website_mass_mailing', 'calendar'],
    'data': [
        'security/ir.model.access.csv',
        'data/category_data.xml',
        'data/newsletter_data.xml',
        'views/snippets.xml',
        'views/pages.xml',
        'views/layout.xml',
        'views/res_config_settings_views.xml',
        'views/product_templates.xml',
        'views/dynamic_snippets.xml',
        'views/checkout_templates.xml',
        'views/reservation_page.xml',
        'views/calendar_event_views.xml',
        'views/reviews_page.xml',
        'views/menu_page.xml',
        'views/story_page.xml',
        'views/shop_templates.xml',
    ],
    'assets': {
            'web.assets_frontend': [
                'theme_restaurant/static/src/css/theme.css',
                'theme_restaurant/static/src/css/theme_additions.css',
                'theme_restaurant/static/src/css/shop.scss',
                'theme_restaurant/static/src/css/product.scss',
                'theme_restaurant/static/src/css/checkout.scss',
                'theme_restaurant/static/src/js/theme.js',
            ],
            'website.assets_wysiwyg': [
                'theme_restaurant/static/src/css/snippet_editor.css',
            ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',],
    'license': 'LGPL-3',
    'installable': True,
    "auto_install": False,
    "application": False,
}
