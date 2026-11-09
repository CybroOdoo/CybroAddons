# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
## pylint: disable=missing-module-docstring
{
    'name': 'Odoo Professional Report Templates',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': (
        'Customizable professional report templates for '
        'Sales, Purchases, Invoices, and Stock'
    ),
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'account', 'stock', 'purchase'],
    'data': [
        'security/ir.access.csv',
        'data/doc_layout_data.xml',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/stock_picking_views.xml',
        'views/doc_layout_views.xml',
        'report/purchase_traditional_templates.xml',
        'report/purchase_standard_templates.xml',
        'report/purchase_modern_templates.xml',
        'report/purchase_attractive_templates.xml',
        'report/sale_traditional_templates.xml',
        'report/sale_standard_templates.xml',
        'report/sale_modern_templates.xml',
        'report/sale_attractive_templates.xml',
        'report/stock_traditional_templates.xml',
        'report/stock_standard_templates.xml',
        'report/stock_modern_templates.xml',
        'report/stock_attractive_templates.xml',
        'report/account_traditional_templates.xml',
        'report/account_standard_templates.xml',
        'report/account_modern_templates.xml',
        'report/account_attractive_templates.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
