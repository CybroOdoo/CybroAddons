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
    "name": "Vista Backend Theme",
    "version": "20.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Vista Backend Theme is an attractive theme for backend",
    "description": """Minimalist and elegant backend theme for Odoo 20 with
     a colour switcher (blue, green, black) and an app sidebar.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['web', 'mail'],
    "data": [
        'views/assets_views.xml',
        'views/login_templates.xml',
        'views/theme_data_views.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
             'vista_backend_theme/static/src/scss/palette_blue.scss'),
            ('before', 'web/static/src/scss/primary_variables.scss',
             'vista_backend_theme/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_frontend': [
            'vista_backend_theme/static/src/scss/login.scss',
        ],
        'web.assets_backend': [
            'vista_backend_theme/static/src/scss/theme.scss',
            'vista_backend_theme/static/src/js/systray.js',
            'vista_backend_theme/static/src/xml/systray_templates.xml',
            'vista_backend_theme/static/src/js/chrome/sidebar_menu.js',
            'vista_backend_theme/static/src/xml/top_bar_templates.xml',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'auto_install': False,
    'application': False
}
