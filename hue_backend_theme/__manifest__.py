# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    "name": "Hue Backend Theme v16",
    "description": """Minimalist and elegant backend theme for Odoo 16, Backend Theme, Theme""",
    "summary": "Hue backed Theme V16 is an attractive theme for backend",
    "category": "Themes/Backend",
    "version": "16.0.1.0.0",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['base', 'web', 'mail'],
    "data": [
        'views/style.xml',
        'views/res_config_settings.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hue_backend_theme/static/src/components/app_menu/side_menu.xml',
            'hue_backend_theme/static/src/layout/style/login.scss',
            'hue_backend_theme/static/src/layout/style/layout_colors.scss',
            'hue_backend_theme/static/src/components/app_menu/menu_order.css',
            'hue_backend_theme/static/src/layout/style/layout_style.scss',
            'hue_backend_theme/static/src/layout/style/sidebar.scss',
            'hue_backend_theme/static/src/components/app_menu/search_apps.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
