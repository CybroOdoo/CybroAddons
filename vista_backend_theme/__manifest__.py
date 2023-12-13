# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    "name": "Vista Backend Theme",
    "version": "17.0.1.0.0",
    "category": "Themes/Backend",
    "summary": "Vista Backend Theme is an attractive theme for backend",
    "description": """Minimalist and elegant backend theme for Odoo 17, 
     Backend Theme, Theme""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['web', 'mail'],
    "data": [
        'security/ir.model.access.csv',
        'views/icons_views.xml',
        'views/layout_templates.xml',
        'views/theme_data_views.xml',
        'views/assets_views.xml',
        'data/theme_data.xml',
    ],
    'assets': {
        'web.assets_backend': {
            '/vista_backend_theme/static/src/scss/theme.scss',
            '/vista_backend_theme/static/src/js/systray.js',
            '/vista_backend_theme/static/src/js/chrome/sidebar_menu.js',
            '/vista_backend_theme/static/src/xml/systray_templates.xml',
            '/vista_backend_theme/static/src/xml/top_bar_templates.xml',
        },
        'web.assets_frontend': {
            '/vista_backend_theme/static/src/scss/login.scss',
            '/vista_backend_theme/static/src/scss/login.scss',
        },
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/theme_screenshot.jpg',
    ],
    'license': 'LGPL-3',
    'pre_init_hook': 'test_pre_init_hook',
    'post_init_hook': 'test_post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': False
}
