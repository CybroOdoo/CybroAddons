# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    "name": "Artify Backend Theme",
    "version": "19.0.1.0.1",
    "description": "Minimalist and elegant backend "
                   "theme for Odoo 19, Backend Theme",
    "summary": "Artify Backend Theme V19 is an attractive theme for backend",
    "category": "Themes/Backend",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['base', 'web', 'mail'],
    "data": [
        'views/icons.xml',
        'views/layout.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'artify_backend_theme/static/src/scss/login.scss',
        ],
        'web.assets_backend': [
            'artify_backend_theme/static/src/xml/styles.xml',
            'artify_backend_theme/static/src/xml/top_bar.xml',
            'artify_backend_theme/static/src/scss/variables.scss',
            'artify_backend_theme/static/src/scss/navigation_bar.scss',
            'artify_backend_theme/static/src/scss/style.scss',
            'artify_backend_theme/static/src/scss/sidebar.scss',
            'artify_backend_theme/static/src/js/NavBarArtify.js',
            'artify_backend_theme/static/src/scss/override.scss',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'icon': 'static/description/icon.png',
    'license': 'LGPL-3',
    'pre_init_hook': 'init_hooks',
    'post_init_hook': 'init_hooks',
    'installable': True,
    'application': False,
    'auto_install': False,
}
