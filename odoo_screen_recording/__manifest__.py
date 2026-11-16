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
    'name': "Odoo Screen Recording",
    'version': '20.0.1.0.0',
    'category': "Extra Tools",
    'summary': """Record your screen at any time and store it for further use
     in Odoo""",
    'description': 'Screen recording in Odoo helps to record multiple screens '
                   'at a time to store or monitor the screen activities',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'web'],
    'data': [
        'security/ir.access.csv',
        'views/video_store_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/odoo_screen_recording/static/src/js/button_systray.js',
            '/odoo_screen_recording/static/src/xml/button_systray.xml',
            '/odoo_screen_recording/static/src/js/video_preview_widget.js',
            '/odoo_screen_recording/static/src/xml/video_preview_widget.xml',
        ]
    },
    'images': [
            'static/description/banner.jpg'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
