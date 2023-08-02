# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sigha CK (odoo@cybrosys.com)
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
###############################################################################
{
    "name": "Blueberry Backend Theme",
    "version": "15.0.1.0.0",
    "category": "Themes/Backend",
    "summary": """Blueberry Backend Theme is an attractive and modern 
     eCommerce Website theme""",
    "description": "Blueberry Backend Theme Is A Ultimate Theme for Odoo 15."
     "This Theme Will Give You A New Experience With Odoo",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "depends": ['web', 'portal'],
    "assets": {
        'web.assets_backend': [
            'backend_theme_odoo12/static/src/scss/theme_style_backend.scss',
            'backend_theme_odoo12/static/src/js/search_apps.js',
            'backend_theme_odoo12/static/src/js/sidebar_menu.js',
        ],
        'web.assets_frontend': [
            'backend_theme_odoo12/static/src/scss/theme_style.scss',
        ],
        'web.assets_qweb': [
            'backend_theme_odoo12/static/src/xml/base_ext.xml',
            'backend_theme_odoo12/static/src/xml/sidebar_menu_templates.xml'
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
