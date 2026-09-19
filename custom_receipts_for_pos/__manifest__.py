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
    'name': 'Custom Receipts For POS',
    'version': '20.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Customizable Point of Sale Receipt Designs with multiple 
    templates support""",
    'description': """The Custom Receipts for POS module empowers users to 
    create and manage highly customized receipt designs tailored to their brand 
    identity. By leveraging Odoo's modern OWL framework, this module provides
    a flexible way to update receipt layouts without complex technical overhead.
    Key Features:
    - Customizable Receipts: Design unique templates for different Point of Sale 
    instances.
    - Multiple Templates Support: Easily switch between various receipt styles.
    - Professional Templates: Enhances the customer experience with 
    well-formatted and stylish receipts.
    - Seamless Integration: Works natively with Odoo 20 Point of Sale.
    - Reliable Fallback: Automatically reverts to the default POS receipt if a 
    custom design is not selected.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.access.csv',
        'data/pos_receipt_data.xml',
        'views/pos_receipt_views.xml',
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'custom_receipts_for_pos/static/src/plugins/pos_ticket_printer_plugin.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
