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
    'name': 'Sale Order Invoice Linker',
    'version': '20.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'This module is designed to provide users with the ability to '
               'manually link invoices to specific sales orders.',
    'description': "This module enhances user functionality within the Odoo "
                   "platform by enabling manual linkage of invoices to "
                   "specific sales orders. It empowers users to conveniently "
                   "associate invoices with their corresponding sales orders, "
                   "facilitating accurate record-keeping and streamlined "
                   "transaction management. Additionally, the module "
                   "incorporates validation checks to ensure data integrity, "
                   "such as verifying product consistency and detecting "
                   "partner mismatches between invoices and associated sales "
                   "orders.",
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'account'],
    'data': [
        'security/ir.access.csv',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'wizard/link_invoice_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

