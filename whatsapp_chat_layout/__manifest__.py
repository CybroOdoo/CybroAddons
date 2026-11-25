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
#############################################################################
{
    'name': 'WhatsApp Chat Layout in Odoo Discuss',
    'version': '20.0.1.0.0',
    'category': 'Discuss',
    'summary': 'WhatsApp-style chat interface for Odoo Discuss with custom themes and wallpapers',
    'description': """
Transforms the Odoo Discuss module into a WhatsApp-style chat interface.

Features:
- WhatsApp-inspired sidebar with tabs for Mail, Direct Messages, Channels and Video Calls
- Dynamic background color and layout (accent) color configurable per company via Settings
- Custom background image (wallpaper) support with automatic MIME-type detection
- Transparent chat canvas so the wallpaper shows cleanly behind conversation bubbles
- Frosted-glass message cards and date pills when a wallpaper is active
- Current-user avatar displayed in the sidebar header
- Fully integrated with Odoo 20 Discuss and OWL 3 component architecture
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['mail', 'base_setup'],
    'data': [
        'views/res_config_settings_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'whatsapp_chat_layout/static/src/js/discuss_sidebar.js',
            'whatsapp_chat_layout/static/src/xml/discuss_sidebar.xml',
            'whatsapp_chat_layout/static/src/js/discuss_container.js',
            'whatsapp_chat_layout/static/src/js/Thread.js',
            'whatsapp_chat_layout/static/src/js/composer_patch.js',
            'whatsapp_chat_layout/static/src/xml/composer.xml',
            'whatsapp_chat_layout/static/src/css/discuss.css',
            'whatsapp_chat_layout/static/src/css/thread.css',
            'whatsapp_chat_layout/static/src/css/color.css',
        ],
        'web.assets_tests': [
            'whatsapp_chat_layout/static/tests/tours/**/*',
        ],
    },
    'images': [
        'static/description/banner.jpg',
        'static/description/icon.png',
        'static/description/assets/screenshots/c1.png',
        'static/description/assets/screenshots/c2.png',
        'static/description/assets/screenshots/c3.png',
        'static/description/assets/screenshots/c4.png',
        'static/description/assets/screenshots/c5.png',
        'static/description/assets/screenshots/c6.png',
        'static/description/assets/screenshots/c7.png',
        'static/description/assets/screenshots/c8.png',
        'static/description/assets/screenshots/c9.png',
        'static/description/assets/screenshots/c10.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
