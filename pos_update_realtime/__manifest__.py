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
    'name': 'POS Product Real-time Updates',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Real-time product updates in POS using bus notifications',
    'description': """This module allows users to change products in real time across all active POS sessions.
                    Any updates made to a product are instantly reflected without restarting or refreshing sessions.
                    It ensures seamless synchronization and consistent product data across all terminals.
                    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'point_of_sale', 'bus'],
    'website': 'https://www.cybrosys.com',
    'images': ['static/description/banner.jpg'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_update_realtime/static/src/js/pos_realtime_posstore.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
