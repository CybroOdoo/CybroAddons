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
#############################################################################
{
    "name": "Chameleon Multi Color Backend Theme",
    "version": "20.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Configurable multi color backend theme for Odoo 20",
    "description": """
        Configurable multi color backend theme for Odoo 20, 
        Only Admin can have the role to create, update, and removing the themes.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "depends": ['web', 'mail'],
    "data": [
        'security/security_groups.xml',
        'security/ir.access.csv',
        'data/theme_data.xml',
        'views/login_templates.xml',
    ],
    "assets": {
        'web.assets_backend': [
            'multicolor_backend_theme/static/src/xml/sidebar_menu_icon.xml',
            'multicolor_backend_theme/static/src/xml/systray_ext.xml',
            'multicolor_backend_theme/static/src/scss/theme_style_backend.scss',
            'multicolor_backend_theme/static/src/css/backend.css',
            'multicolor_backend_theme/static/src/js/sidebar_menu.js',
            'multicolor_backend_theme/static/src/js/search_apps.js',
            'multicolor_backend_theme/static/src/js/systray_item.js',
        ],
        'web.assets_frontend': [
            'multicolor_backend_theme/static/src/scss/theme_style.scss',
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
