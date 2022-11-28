# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    "name": "Infinito Backend Theme",
    "description": """Utmost and dynamic backend theme for Odoo 16""",
    "summary": """The Backend Theme Infinito Is A Dynamic And Ultimate Theme
     For Your Odoo V16. This Theme Will Give You A New Experience With Odoo.
      Main Highlight Of The Theme Is You Can Dynamically Change The Colors,
       Views, Buttons, Different Types Sidebar...Etc""",
    "category": "Themes/Backend",
    "version": "16.0.1.0.0",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['web', 'mail'],
    "data": [
        'views/assets.xml',
        'views/layout.xml',
        'views/base_pwa.xml',
        'views/icons.xml',
    ],
    'assets': {
        'web._assets_primary_variables': {
            'backend_theme_infinito/static/src/scss/theme_variables.scss',
        },
        'web.assets_backend': {
            '/backend_theme_infinito/static/src/xml/systray.xml',
            '/backend_theme_infinito/static/src/xml/views.xml',
            '/backend_theme_infinito/static/src/xml/theme_editor.xml',
            '/backend_theme_infinito/static/src/xml/studio_elements.xml',
            '/backend_theme_infinito/static/src/xml/ThemeStudioMenu.xml',
            '/backend_theme_infinito/static/src/xml/style_add.xml',
            '/backend_theme_infinito/static/src/xml/sidebar.xml',
            '/backend_theme_infinito/static/src/xml/MenuBookmark.xml',

            'https://fonts.googleapis.com/css2?family=Poppins:wght@100;200;300;400;500;600;700;800;900&display=swap',
            '/backend_theme_infinito/static/src/css/style.css',
            '/backend_theme_infinito/static/src/css/loaders.css',
            'backend_theme_infinito/static/src/scss/sidebar.scss',
            'backend_theme_infinito/static/src/scss/responsive.scss',
            'backend_theme_infinito/static/src/scss/theme_date_picker.scss',
            'backend_theme_infinito/static/src/scss/theme_styles.scss',
            'backend_theme_infinito/static/src/scss/theme_rtl.scss',
            'backend_theme_infinito/static/src/scss/app_menu.scss',
            'backend_theme_infinito/static/src/scss/extra_styles.scss',
            'backend_theme_infinito/static/src/scss/views.scss',
            '/backend_theme_infinito/static/src/js/systray.js',
            '/backend_theme_infinito/static/src/js/loaders.js',
            '/backend_theme_infinito/static/src/js/theme_editor.js',
            '/backend_theme_infinito/static/src/js/ThemeStudioWidget.js',
            '/backend_theme_infinito/static/src/js/Tool.js',
            '/backend_theme_infinito/static/src/js/VisualEditor.js',
            '/backend_theme_infinito/static/src/js/change.js',
            '/backend_theme_infinito/static/src/js/style_add.js',
            '/backend_theme_infinito/static/src/js/sidebar.js',
            '/backend_theme_infinito/static/src/js/navbar.js',
            '/backend_theme_infinito/static/src/js/theme_editor_sidebar.js',
            '/backend_theme_infinito/static/src/js/recentApps.js',
            '/backend_theme_infinito/static/src/js/timepicker.js',
            '/backend_theme_infinito/static/src/js/MenuBookmark.js',
            '/backend_theme_infinito/static/src/js/AdvancedFeautres.js',
            '/backend_theme_infinito/static/src/js/theme_studio_action.js',
            '/backend_theme_infinito/static/src/js/ThemeStudioMenu.js',
            '/backend_theme_infinito/static/src/js/variables.js',
        },
    },
    'post_init_hook': 'icons_post_init_hook',
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
