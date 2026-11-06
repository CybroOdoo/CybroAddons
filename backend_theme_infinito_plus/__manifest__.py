# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Infinito Plus Backend Theme',
    'summary': 'Adds fonts, chatbox positioning, animations, view refresh, '
               'and language switching to the Infinito Backend Theme.',
    'description': """Extends the Infinito Backend Theme for Odoo 19 with
Google Fonts, chatbox positioning, Kanban animations, view refreshing,
and language switching.""",
    'category': 'Themes/Backend',
    'version': '19.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['backend_theme_infinito'],
    'data': [
        'security/ir.model.access.csv',
        'views/layout.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'backend_theme_infinito_plus/static/src/xml/ListViewRefresh.xml',
            'backend_theme_infinito_plus/static/src/xml/systray.xml',
            'backend_theme_infinito_plus/static/src/css/style.css',
            'backend_theme_infinito_plus/static/src/js/animation.js',
            'backend_theme_infinito_plus/static/src/js/navbar.js',
            'backend_theme_infinito_plus/static/src/js/Sidebar.js',
            'backend_theme_infinito_plus/static/src/js/AdvancedFeatures.js',
            'backend_theme_infinito_plus/static/src/js/systray.js',
            'backend_theme_infinito_plus/static/src/js/ThemeStudioMenu.js',
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
