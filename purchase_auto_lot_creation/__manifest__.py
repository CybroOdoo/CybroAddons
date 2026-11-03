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
    'name': 'Purchase Auto Lot Creation',
    'version': '20.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': "Generate product lots during the purchasing process "
               "automatically",
    'description':
        "This module automates the creation of product lots during the "
        "purchase workflow. When a purchase order is confirmed, the system "
        "automatically generates lot numbers. It helps streamline inventory "
        "tracking, ensures better traceability, and reduces manual effort in "
        "lot management during the goods receipt process.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['purchase_stock'],
    'data': [
        'security/ir.access.csv',
        'views/custom_stock_lot_views.xml',
        'views/purchase_order_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
