# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
###############################################################################
{
    'name': 'Purchase Auto Lot Creation',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': "Generate product lots during the purchasing process "
               "automatically",
    'description':
        "This module automates the creation of product lots during the purchase workflow. "
        "When a purchase order is confirmed, the system automatically generates lot numbers "
        "It helps streamline inventory tracking, ensures better traceability, and reduces "
        "manual effort in lot management during the goods receipt process.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['purchase_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_stock_lot_views.xml',
        'views/purchase_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_auto_lot_creation/static/css/fullcalendar_custom.css']
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
