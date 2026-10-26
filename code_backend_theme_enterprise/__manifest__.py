# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aswin A K (odoo@cybrosys.com)
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
    "name": "Code Backend Theme Enterprise",
    "version": "20.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Minimalist and elegant backend theme for Odoo Enterprise",
    "description": """Minimalist and elegant backend theme for Odoo Backend""",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["web_enterprise", "web"],
    "data": [
        'views/base_menus.xml',
        'data/menu_icons.xml',
        'views/login_templates.xml',
    ],
    'assets': {
        # Theme colours and font, applied through Odoo/Bootstrap variables
        'web._assets_primary_variables': [
            ('before', 'web_enterprise/static/src/scss/primary_variables.scss',
             'code_backend_theme_enterprise/static/src/scss/primary_variables.scss'),
        ],
        'web.dark_mode_variables': [
            ('before', 'code_backend_theme_enterprise/static/src/scss/primary_variables.scss',
             'code_backend_theme_enterprise/static/src/scss/primary_variables.dark.scss'),
        ],
        'web.assets_backend': [
            "code_backend_theme_enterprise/static/src/scss/fonts.scss",
            # Design tokens first: every other stylesheet reads them
            "code_backend_theme_enterprise/static/src/scss/backend/tokens.scss",
            "code_backend_theme_enterprise/static/src/scss/backend/layout.scss",
            "code_backend_theme_enterprise/static/src/scss/backend/navbar.scss",
            "code_backend_theme_enterprise/static/src/scss/backend/sidebar.scss",
            "code_backend_theme_enterprise/static/src/scss/backend/home_menu.scss",
            "code_backend_theme_enterprise/static/src/scss/backend/form.scss",
            "code_backend_theme_enterprise/static/src/scss/backend/views.scss",
            "code_backend_theme_enterprise/static/src/xml/top_bar_templates.xml",
            "code_backend_theme_enterprise/static/src/js/chrome/sidebar.js",
        ],
        'web.assets_frontend': [
            "code_backend_theme_enterprise/static/src/scss/fonts.scss",
            "code_backend_theme_enterprise/static/src/scss/login.scss",
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
