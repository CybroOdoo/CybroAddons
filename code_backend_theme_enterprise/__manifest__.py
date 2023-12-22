# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADVAITH BG (odoo@cybrosys.com)
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
    "version": "17.0.1.0.0",
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
    ],
    'assets': {
        'web.assets_backend': [
            "code_backend_theme_enterprise/static/src/xml/"
            "top_bar_templates.xml",
            "code_backend_theme_enterprise/static/src/xml/"
            "sidebar_templates.xml",
            "code_backend_theme_enterprise/static/src/scss/sidebar.scss",
            "code_backend_theme_enterprise/static/src/js/chrome/sidebar.js",
            "code_backend_theme_enterprise/static/src/js/fields/colors.js",
            "code_backend_theme_enterprise/static/src/scss/theme_accent.scss",
            "code_backend_theme_enterprise/static/src/scss/datetimepicker.scss",
            "code_backend_theme_enterprise/static/src/scss/theme.scss",
            "https://fonts.googleapis.com/css2?family=Poppins:wght@400;700"
            "&display=swap",
        ],
        'web.assets_frontend': [
            "code_backend_theme_enterprise/static/src/scss/login.scss",
            "https://fonts.googleapis.com/css2?family=Poppins:wght@400;700"
            "&display=swap",
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
    'pre_init_hook': 'test_pre_init_hook',
    'post_init_hook': 'test_post_init_hook',
}
