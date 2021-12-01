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
    "name": "Code Backend Theme V15 Enterprise",
    "summary": "Minimalist and elegant backend theme for Odoo 15 Enterprise",
    "description": """Minimalist and elegant backend theme for Odoo 15 Backend Theme Enterprise, Enterprise Theme, Backend Theme, Enterprise Backend Theme, V15 Theme""",
    "category": "Themes/Backend",
    "version": "15.0.1.0.0",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['base', 'web_enterprise', 'web'],
    "data": [
        'views/icons.xml',
    ],

    'assets': {
        'web.assets_backend': [
            "code_backend_theme_enterprise/static/src/scss/theme_accent.scss",
            "code_backend_theme_enterprise/static/src/scss/navigation_bar.scss",
            "code_backend_theme_enterprise/static/src/scss/datetimepicker.scss",
            "code_backend_theme_enterprise/static/src/scss/theme.scss",
            "code_backend_theme_enterprise/static/src/scss/sidebar.scss",
            "code_backend_theme_enterprise/static/src/js/chrome/sidebar.js",
            "code_backend_theme_enterprise/static/src/js/fields/basic_fields.js",
            "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&amp;display=swap",
        ],
        'web.assets_qweb': [
            'code_backend_theme_enterprise/static/src/xml/top_bar.xml',
            'code_backend_theme_enterprise/static/src/xml/sidebar.xml',
        ],
        'web.assets_frontend': [
            "code_backend_theme_enterprise/static/src/scss/login.scss",
            "https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&amp;display=swap",
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'pre_init_hook': 'test_pre_init_hook',
    'post_init_hook': 'test_post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
