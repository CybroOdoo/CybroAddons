# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################

{
    "name": "Chameleon Multi Color Backend Theme",
    "version": "15.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Configurable multi color backend theme for Odoo 15",
    "description": """
        Configurable multi color backend theme for Odoo 15
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    'images': [
            'static/description/banner.png',
            'static/description/theme_screenshot.png',
        ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
    "depends": [
        'website',
        'portal',
        'mail',

    ],
    "data": [
        'security/ir.model.access.csv',
        'data/theme_data.xml',
        'views/login_templates.xml',
    ],
    "assets": {
        'web.assets_backend': [
            '/multicolor_backend_theme/static/src/scss/theme_style_backend.scss',
            '/multicolor_backend_theme/static/src/css/img_picker.css',
            '/multicolor_backend_theme/static/src/wcolpick/wcolpick.css',
            '/multicolor_backend_theme/static/src/js/sidebar_menu.js',
            '/multicolor_backend_theme/static/src/wcolpick/wcolpick.js',
            '/multicolor_backend_theme/static/src/js/jquery_img_picker.js',
            '/multicolor_backend_theme/static/src/js/search_apps.js',
            '/multicolor_backend_theme/static/src/js/systray_theme_menu.js'

        ],
        'web.assets_frontend': [
            '/multicolor_backend_theme/static/src/scss/theme_style.scss',
            '/multicolor_backend_theme/static/src/js/login_page.js'
        ],
        'web.assets_qweb': [
             'multicolor_backend_theme/static/src/xml/base_ext.xml',
             'multicolor_backend_theme/static/src/xml/sidebar_menu_icon.xml',
             'multicolor_backend_theme/static/src/xml/systray_ext.xml',
        ],
    },


}
