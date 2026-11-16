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
    'name': 'POS Booking Order',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Create pickup or delivery booking orders from POS session and confirm as POS orders',
    'description': """The module helps you to book orders from Shop, Bar/Restaurant in POS. User can create pickup or delivery orders, and later confirm booked orders to POS orders.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'views/pos_config_views.xml',
        'views/book_order_views.xml',
        'views/pos_order_views.xml',
        'views/pos_order_receipt.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_book_order/static/src/**',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
