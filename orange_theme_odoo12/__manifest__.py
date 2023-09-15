# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    "name": "Outrageous Orange Backend Theme",
    "description": """Backend theme for Odoo 16.0 community edition.""",
    "summary": "Outrageous Orange Backend Theme",
    'version': '16.0.2.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "category": "Themes/Backend",
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    "depends": [
        'web',
        'portal',
    ],
    "data": [
        'views/login_templates.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'orange_theme_odoo12/static/src/scss/sidebar.scss',
            'orange_theme_odoo12/static/src/scss/theme_style_backend.scss',
            'orange_theme_odoo12/static/src/js/chrome/sidebar_menu.js',
            'orange_theme_odoo12/static/src/js/chrome/search_apps.js',
            'orange_theme_odoo12/static/src/xml/styles.xml',
            'orange_theme_odoo12/static/src/xml/top_bar.xml',
        ],
        'web.assets_frontend': [
            'orange_theme_odoo12/static/src/scss/theme_style.scss',
        ],

    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
