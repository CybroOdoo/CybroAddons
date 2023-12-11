# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Dynamic Financial Reports V16',
    'version': '16.0.1.0.10',
    'category': 'Accounting',
    'live_test_url': 'https://www.youtube.com/watch?v=gVQi9q9Rs-E&t=5s',
    'summary': """Dynamic Financial Reports with drill 
                down and filters– Community Edition""",
    'description': "Dynamic Financial Reports, DynamicFinancialReports, FinancialReport, Accountingreports, odoo reports, odoo"
                   "This module creates dynamic Accounting General Ledger, Trial Balance, Balance Sheet "
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
        'views/reports_config_view.xml',
        'report/trial_balance.xml',
        'report/general_ledger.xml',
        'report/cash_flow_report.xml',
        'report/financial_report_template.xml',
        'report/partner_ledger.xml',
        'report/ageing.xml',
        'report/daybook.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dynamic_accounts_report/static/src/css/report.css',
            'dynamic_accounts_report/static/src/js/action_manager.js',
            'dynamic_accounts_report/static/src/js/general_ledger.js',
            'dynamic_accounts_report/static/src/js/trial_balance.js',
            'dynamic_accounts_report/static/src/js/cash_flow.js',
            'dynamic_accounts_report/static/src/js/financial_reports.js',
            'dynamic_accounts_report/static/src/js/partner_ledger.js',
            'dynamic_accounts_report/static/src/js/ageing.js',
            'dynamic_accounts_report/static/src/js/daybook.js',
            'dynamic_accounts_report/static/src/xml/general_ledger_view.xml',
            'dynamic_accounts_report/static/src/xml/trial_balance_view.xml',
            'dynamic_accounts_report/static/src/xml/cash_flow_view.xml',
            'dynamic_accounts_report/static/src/xml/financial_reports_view.xml',
            'dynamic_accounts_report/static/src/xml/partner_ledger_view.xml',
            'dynamic_accounts_report/static/src/xml/ageing.xml',
            'dynamic_accounts_report/static/src/xml/daybook.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': '_load_account_details_post_init_hook',
    'uninstall_hook': 'unlink_records_financial_report'
}
