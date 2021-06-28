# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Dynamic Financial Reports',
    'version': '13.0.1.0.1',
    'category': 'Accounting',
    'summary': """Dynamic Financial Reports with drill 
                down and filters– Community Edition""",
    'description': "This module creates dynamic Accounting General Ledger, Trial Balance, Balance Sheet "
                   "Proft and Loss, Cash Flow Statements, Partner Ledger,"
                   "Partner Ageing, Day book"
                   "Bank book and Cash book reports in Odoo 14 community edition.",
    'author': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'depends': ['base', 'base_accounting_kit'],
    'data': [
        'security/ir.model.access.csv',
        'views/templates.xml',
        'views/views.xml',
        'views/kit_menus.xml',
        'report/trial_balance.xml',
        'report/general_ledger.xml',
        'report/cash_flow_report.xml',
        'report/financial_report_template.xml',
        'report/partner_ledger.xml',
        'report/ageing.xml',
        'report/daybook.xml',
    ],
    'qweb': [
            'static/src/xml/general_ledger_view.xml',
            'static/src/xml/trial_balance_view.xml',
            'static/src/xml/cash_flow_view.xml',
            'static/src/xml/financial_reports_view.xml',
            'static/src/xml/partner_ledger_view.xml',
            'static/src/xml/ageing.xml',
            'static/src/xml/daybook.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
