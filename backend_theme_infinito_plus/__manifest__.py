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
    'name': 'Backend Theme Infinito Plus',
    'version': "15.0.1.0.0",
    'category': 'Extra Tools',
    'summary': 'The Backend Theme Infinito Is A Dynamic And Ultimate Theme'
               'For Your Odoo V15. This Theme Will Give You A New Experience '
               'With Odoo.Main Highlight Of The Theme Is You Can Dynamically '
               'Change The Fonts,Animations, Languages,...Etc',
    'description': """Utmost and dynamic backend theme for Odoo 15""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'backend_theme_infinito'],
    'data': [
        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_backend': {
            'backend_theme_infinito_plus/static/src/css/chatter.css',
            'backend_theme_infinito_plus/static/src/css/font.css',
            'backend_theme_infinito_plus/static/src/scss/animation.scss',
            'backend_theme_infinito_plus/static/src/js/AdvancedFeautres.js',
            'backend_theme_infinito_plus/static/src/js/navbar.js',
            'backend_theme_infinito_plus/static/src/js/ThemeStudioMenu.js',
            'backend_theme_infinito_plus/static/src/js/systray.js'
        },
        'web.assets_qweb': {
            'backend_theme_infinito_plus/static/src/xml/sidebar_templates.xml',
            'backend_theme_infinito_plus/static/src/xml/AddGoogleFonts_templates.xml',
            'backend_theme_infinito_plus/static/src/xml/refresh_templates.xml',
            'backend_theme_infinito_plus/static/src/xml/systray_templates.xml'
        }
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
