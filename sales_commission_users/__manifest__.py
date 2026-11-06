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
    'name': 'Sales Commission',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Manage and calculate sales commissions for salespersons in Odoo 20',
    'description': """Allows creation and calculation of sales commission based on
        Product, Partner affiliation, and Sale Order line discounts for salespersons
        in Odoo 20.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale', 'account'],
    'data': [
        'security/ir.access.csv',
        'wizard/sales_commission_report_views.xml',
        'views/sales_commission_views.xml',
        'views/commission_lines_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'report/sales_commission_action.xml',
        'report/sales_commission_templates.xml',
        'views/sales_commission_menus.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
