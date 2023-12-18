# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Advanced Sales Reports',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': """This Module Helps to Generate Advanced sales reports""",
    'description': """This module helps you to print reports like Sales Analysis, 
     Sales By Category, Sales Indent, Sales Invoice ,Product Profit ,
     Hourly Sales in PDF and XLSX format.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
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
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
