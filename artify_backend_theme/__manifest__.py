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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
{
    "name": "Artify Backend Theme",
    "version": "20.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Artify Backend Theme V20 is an attractive theme for backend",
    "description": "Minimalist and elegant backend theme for Odoo 20",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['base', 'web', 'mail'],
    "data": [
        'views/icons.xml',
    ],
    'assets': {
        # Theme colours, applied through Odoo/Bootstrap variables
        'web._assets_primary_variables': [
            ('prepend', 'artify_backend_theme/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_frontend': [
            'artify_backend_theme/static/src/scss/login.scss',
        ],
        'web.assets_backend': [
            # Design tokens first: every other stylesheet reads them
            'artify_backend_theme/static/src/scss/backend/tokens.scss',
            'artify_backend_theme/static/src/scss/backend/navbar.scss',
            'artify_backend_theme/static/src/scss/backend/sidebar.scss',
            'artify_backend_theme/static/src/scss/backend/views.scss',
            ('after', 'web/static/src/webclient/navbar/navbar.xml',
             'artify_backend_theme/static/src/xml/top_bar.xml'),
            'artify_backend_theme/static/src/js/NavBarArtify.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'post_init_hook': 'init_hooks',
    'installable': True,
    'auto_install': False,
    'application': False,
}
