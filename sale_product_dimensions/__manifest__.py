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
    'name': 'Sale Product Dimensions',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': "Add length, width and area fields with area-based pricing "
               "across Sales, Purchase, Manufacturing and Invoices",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'purchase', 'mrp', 'account'],
    'data': [
        'views/sale_order_views.xml',
        'views/sale_order_report_templates.xml',
        'views/purchase_order_views.xml',
        'views/purchase_order_report_template.xml',
        'views/mrp_production_views.xml',
        'views/mrp_production_report_templates.xml',
        'views/account_move_views.xml',
        'views/report_invoice_document.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
