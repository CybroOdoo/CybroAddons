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
    'name': 'Remove Order Line In POS',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """POS Delete Order Line, Remove Order Line, POS Clear Cart, Clear All Order Lines, Point of Sale, Odoo POS, Odoo20 POS, Odoo20 Point of Sale""",
    'description': """
     Remove order lines from the Point of Sale cart with a single click. Each
     line of the cart gets a delete button, and a Clear All button removes
     every line of the current order after a confirmation. Removing a combo
     item removes the whole combo, like the numpad does, and the delete
     buttons only appear in the cart, not on receipts or the orders list.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_delete_orderline/static/src/**/*',
        ],
        'web.assets_tests': [
            'pos_delete_orderline/static/tests/tours/**/*',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
