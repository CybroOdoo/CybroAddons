# -*- coding: utf-8 -*-
{
    "name": "Dodger Blue Backend Theme",
    "summary": "Outrageous Blue Backend Theme",
    "version": "16.0.1.0.0",
    "category": "Themes/Backend",
    "website": "https://www.cybrosys.com",
    "description": """Backend theme for Odoo 16.0 community edition. Blue theme blue backend theme odoo backend theme""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "depends": [
        'website',
        'portal',

    ],
    "data": [
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': {
            'dodger_blue/static/src/scss/theme_style.scss',
        },
        'web.assets_backend': {
            'dodger_blue/static/src/js/sidebar_menu.js',
            'dodger_blue/static/src/scss/theme_style_backend.scss',

            'dodger_blue/static/src/xml/base_ext.xml',
            'dodger_blue/static/src/xml/sidebar_menu_icon.xml',
        },

    },

    'license': 'LGPL-3',
    'images': ['static/description/banner.png',
               'static/description/theme_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,

}
