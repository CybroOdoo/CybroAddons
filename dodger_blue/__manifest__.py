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
    "name": "Dodger Blue Backend Theme",
    "version": "20.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Blue backend theme with a searchable application sidebar",
    'description': 'A longer description of what this theme provides.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    "website": "https://www.cybrosys.com",
    "depends": ['web'],
    "data": [
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'dodger_blue/static/src/scss/theme_style.scss',
        ],
        'web.assets_backend': [
            'dodger_blue/static/src/js/sidebar_menu.js',
            'dodger_blue/static/src/scss/theme_style_backend.scss',
            'dodger_blue/static/src/scss/navbar_controls.scss',
            'dodger_blue/static/src/xml/sidebar_menu_icon_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg',
               'static/description/theme_screenshot.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
