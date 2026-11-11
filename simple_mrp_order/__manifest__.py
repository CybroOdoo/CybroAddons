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
    'name': 'Simple Manufacturing Orders',
    'version': '20.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Create Manufacturing Orders Easily',
    'description': """This module allows you to create manufacturing orders
without taking the work orders or work centers.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'stock'],
    'data': [
        'security/simple_mrp_order_groups.xml',
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'data/stock_location_data.xml',
        'views/mrp_order_views.xml',
        'views/simple_mrp_bom_views.xml',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
