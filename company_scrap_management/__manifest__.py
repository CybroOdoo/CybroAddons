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
    'name': 'Scrap Management',
    'version': '20.0.1.0.0',
    'category': 'Industries',
    'summary': 'Manage Scrap in a company',
    'description': """Module helps to dismantle the product having bom and move
     the useful parts to the stock""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'stock', 'mrp'],
    'data': [
        'security/ir.access.csv',
        'data/ir_sequence_data.xml',
        'views/scrap_management_line_views.xml',
        'views/scrap_management_views.xml',
        'views/stock_scrap_views.xml',
        'report/scrap_management_template.xml',
        'report/scrap_management_state_wise_template.xml',
        'report/scrap_management_reports.xml',
        'report/scrap_management_product_wise_template.xml',
        'wizard/scrap_management_report_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
