# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Advanced Sales Reports',
    'version': '14.0.1.0.0',
    'summary': 'Advanced sales reports for odoo 14',
    'description': """module helps you to print reports like Sales Analysis, Sales By Category,
                        Sales Indent, Sales Invoice ,Product Profit ,Hourly Sales in PDF and XLSX format.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'category': 'Sales',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'base','account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_report.xml',
        'wizard/sale_invoice.xml',
        'wizard/sale_analysis.xml',
        'wizard/weekly_wise.xml',
        'wizard/sale_category.xml',
        'wizard/sale_indent.xml',
        'views/report_view.xml',
        'views/action_manager.xml',
        'report/sale_reports.xml',
        'report/invoice_analysis_template.xml',
        'report/sales_indent_template.xml',
        'report/sale_profit_template.xml',
        'report/sales_category_template.xml',
        'report/sales_analysis_template.xml',
        'report/sales_weekly_template.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
