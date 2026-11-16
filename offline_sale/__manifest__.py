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
    'name': 'Offline Sales',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Offline-first sales management for high-volume sales and offline use',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'product', 'web', 'auth_totp'],
    'data': [
        'data/mail_template_data.xml',
        'views/offline_sale_menus.xml',
        'views/offline_sale_assets.xml',
        'views/sale_order_views.xml',
        'views/login_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
             'offline_sale/static/src/css/fonts.css',
             'offline_sale/static/src/js/main_backend_handler.js',
             'offline_sale/static/src/js/systray_offline_button.js',
             'offline_sale/static/src/xml/systray_offline_button.xml',
        ],
        'offline_sale.assets': [
            'offline_sale/static/src/app/css/tailwind.css',
            'offline_sale/static/src/app/css/main.css',
            'offline_sale/static/src/app/js/offline_sale_app.js',
            'offline_sale/static/src/app/js/main.js',
            'offline_sale/static/src/app/xml/main.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
