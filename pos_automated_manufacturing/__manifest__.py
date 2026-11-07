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
    'name': 'POS Automated Manufacturing',
    'version': '20.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Automate Manufacturing Order creation from POS.',
    'description': """
        This module allows users to create Manufacturing orders (MRP)
        directly from the Point of Sale (POS) interface.
        Features:
        - Configure products to generate MRP orders upon sale.
        - Automatic validation of MRP orders if configured.
        - Linking POS orders with their respective MRP orders.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',

    'depends': ['point_of_sale', 'mrp'],
    'data': [
        'views/product_template_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
