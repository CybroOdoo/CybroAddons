# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
    "name": "Blueberry Backend Theme",
    "version": "19.0.1.0.0",
    "category": "Themes/Backend",
    "summary": """Backend theme for Odoo 19.0 community edition""",
    "description": "Blueberry Backend Theme Is A Ultimate Theme for Odoo 19."
                   "This Theme Will Give You A New Experience With Odoo",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "assets": {
        'web.assets_backend': [
            '/backend_theme_odoo12/static/src/scss/theme_style_backend.scss',
            '/backend_theme_odoo12/static/src/js/search_apps.js',
            '/backend_theme_odoo12/static/src/xml/sidebar_menu_templates.xml',
        ],
        'web.assets_frontend': [
            'backend_theme_odoo12/static/src/scss/theme_style.scss'
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
