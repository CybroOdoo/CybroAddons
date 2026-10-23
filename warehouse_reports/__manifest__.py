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
    'name': 'Warehouse Reports',
    'version': '20.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'All warehouse related PDF and Excel reports for Odoo 20',
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['stock', 'stock_account', 'web'],
    'data': [
        'security/ir.access.csv',
        'report/ir_action_reports.xml',
        'report/stock_valuation_report_templates.xml',
        'report/stock_transfer_report_templates.xml',
        'report/stock_move_report_templates.xml',
        'report/stock_product_report_templates.xml',
        'wizards/stock_valuation_report_views.xml',
        'wizards/stock_move_report_views.xml',
        'wizards/stock_product_report_views.xml',
        'wizards/stock_transfer_report_views.xml',
        'views/warehouse_reports_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'warehouse_reports/static/src/js/stock_excel_report.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
