# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    'name': 'Theme Velora',
    'version': '20.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Luxury fragrances and signature perfumes eCommerce theme with rich snippets and editorial design',
    'description': 'A luxury fragrances and signature perfumes theme for Odoo 20 eCommerce',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['website', 'website_sale', 'website_mass_mailing'],
    'data': [
        'data/menus.xml',
        'data/categories.xml',
        'data/mailing_list.xml',
        'views/layout.xml',
        'views/pages_homepage.xml',
        'views/pages_about.xml',
        'views/pages_bestseller.xml',
        'views/pages_collections.xml',
        'views/pages_contact.xml',
        'views/pages_login.xml',
        'views/ecommerce_templates.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'theme_velora/static/src/css/style.css',
            'theme_velora/static/src/css/about.css',
            'theme_velora/static/src/css/bestseller.css',
            'theme_velora/static/src/css/collections.css',
            'theme_velora/static/src/css/shop.css',
            'theme_velora/static/src/js/script.js',
        ],
        'website.website_builder_assets': [
            'theme_velora/static/src/js/builder_patch.js',
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