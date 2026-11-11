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
    'name': 'Advanced Sales Reports',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Print sales analysis, category, indent, invoice, profit and '
               'hourly reports in PDF and XLSX.',
    'description': 'Adds six wizards under Sales > Reporting to print Sales '
                   'Analysis, Sales Category, Product Sales Indent, Invoice '
                   'Analysis, Product Profit and Hourly Sales reports in PDF '
                   'and XLSX format.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'account'],
    'data': [
        'security/ir.access.csv',
        'wizard/sale_report_advance_views.xml',
        'wizard/sale_report_invoice_views.xml',
        'wizard/sale_report_analysis_views.xml',
        'wizard/sale_report_weekly_views.xml',
        'wizard/sale_report_category_views.xml',
        'wizard/sale_report_indent_views.xml',
        'views/sale_report_advanced_views.xml',
        'report/sale_advanced_reports.xml',
        'report/invoice_analysis_templates.xml',
        'report/sales_indent_templates.xml',
        'report/sale_profit_templates.xml',
        'report/sales_category_templates.xml',
        'report/sales_analysis_templates.xml',
        'report/sales_weekly_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sale_report_advanced/static/src/js/action_manager.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
