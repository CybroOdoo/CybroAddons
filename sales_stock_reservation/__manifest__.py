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
    'name': 'Product Stock Reservation',
    'version': "19.0.1.0.0",
    'category': 'Sales/Sales',
    'summary': "Reserve Product for Sales Order",
    'description': "This module allows sales users to create a product stock reservation from the sales quotation form.",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://www.cybrosys.com",
    'depends': ['sale_management', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_location_data.xml',
        'data/ir_sequence_data.xml',
        'wizard/sale_stock_reservation_views.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}