# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#############################################################################
{
    'name': 'POS Order Line Mass Edit',
    'summary': "Users have the ability to edit POS order lines",
    'version': '20.0.1.0.0',
    'description': """A functionality has been implemented where, upon clicking 
    a button, users have the ability to edit POS order lines. This includes the 
    capability to modify the quantity and price of items, and also add 
    discounts through a popup interface""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Point of Sale',
    'depends': ['base','point_of_sale'],
    "data": [
        "views/pos_config_views.xml",
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_order_line_mass_edit/static/src/**/*',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
