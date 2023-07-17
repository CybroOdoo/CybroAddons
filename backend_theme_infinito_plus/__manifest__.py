# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sigha CK (odoo@cybrosys.com)
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
###############################################################################
{
    'name': "Infinito Plus Backend Theme",
    'description': """Utmost and dynamic backend theme for Odoo 16""",
    'summary': """The Backend Theme Infinito Is A Dynamic And Ultimate Theme
                For Your Odoo V16. This Theme Will Give You A New Experience 
                With Odoo.Main Highlight Of The Theme Is You Can Dynamically 
                Change The Fonts,Animations, Languages,Chatbox Layouts...Etc""",
    'category': "Themes/Backend",
    'version': "16.0.1.0.0",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['backend_theme_infinito', 'web'],
    "data": [
        'security/ir.model.access.csv'
    ],
    'assets': {
        'web.assets_backend': {
            '/backend_theme_infinito_plus/static/src/xml/theme_editor.xml',
            '/backend_theme_infinito_plus/static/src/xml/ListViewRefresh.xml',
            '/backend_theme_infinito_plus/static/src/xml/systray.xml',
            '/backend_theme_infinito_plus/static/src/xml/AddGoogleFonts.xml',
            '/backend_theme_infinito_plus/static/src/xml/font.xml',
            '/backend_theme_infinito_plus/static/src/css/font.css',
            '/backend_theme_infinito_plus/static/src/css/chatter.css',
            '/backend_theme_infinito_plus/static/src/scss/animation.scss',
            '/backend_theme_infinito_plus/static/src/js/navbar.js',
            '/backend_theme_infinito_plus/static/src/js/AdvancedFeatures.js',
            '/backend_theme_infinito_plus/static/src/js/systray.js',
            '/backend_theme_infinito_plus/static/src/js/ThemeStudioMenu.js',
        },
    },
    'images': [
        'static/description/banner.gif',
        'static/description/theme_screenshot.gif',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
