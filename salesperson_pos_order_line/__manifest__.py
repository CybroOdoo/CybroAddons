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
    'name': 'Sales Person On POS Order Line',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Assign salespersons to Point of Sale (POS) order lines',
    'description': 'This module allows you to assign salespersons to order '
                   'lines in the Point of Sale (POS)',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_orderline_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'salesperson_pos_order_line/static/src/js/pos_screen.js',
            'salesperson_pos_order_line/static/src/js/pos_orderline.js',
            'salesperson_pos_order_line/static/src/xml/pos_screen_templates.xml',
            'salesperson_pos_order_line/static/src/xml/orderline_templates.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
