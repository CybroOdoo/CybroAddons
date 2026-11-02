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
    'name': 'Tender Management Sales',
    'version': "20.0.1.0.0",
    'summary': 'Tender Management in Sales and Option to Compare Orders',
    'description': """Tender Management in Sales with features to create sale
    agreements, manage alternative sale orders, and compare orders.""",
    'category': 'Sales',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management'],
    'data': [
        'security/ir.access.csv',
        'data/sale_tender_data.xml',
        'views/tender_sales_views.xml',
        'views/sale_order_views.xml',
        'wizard/tender_sales_create_alternative.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tender_management_sales/static/src/widgets/'
            'sale_order_alternatives_widget.js',
            'tender_management_sales/static/src/widgets/'
            'sale_order_alternatives_widget.scss',
            'tender_management_sales/static/src/widgets/'
            'sale_order_alternatives_widget.xml',
            'tender_management_sales/static/src/views/list/'
            'sale_order_line_compare_list_renderer.js',
            'tender_management_sales/static/src/views/list/'
            'sale_order_line_compare_list_view.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
