# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    'name': 'Odoo 19 Accounting for Community : Financial Report, PDC, Assets, Bank Reconciliation, Lock Dates',
    'version': '19.0.3.3.1',
    'category': 'Accounting',
    'live_test_url': 'https://kit.easyinstance.com/web/login?redirect=/odoo/accounting',
    'summary': """Brings full accounting features back to Odoo 19 Community: financial reports (P&L, Balance Sheet,
                  General Ledger, Trial Balance, Partner Ledger, Aged Receivable/Payable), asset management,
                  budgets, bank statement import, PDC, and customer follow-ups — everything Community is missing.""",
    'description': """ 
      Full Accounting Kit for Odoo 19 Community
      =========================================
      Restores full accounting capabilities to Odoo 19 Community Edition.
        * Financial Reports - Profit and Loss, Balance Sheet, General Ledger,
          Trial Balance, Partner Ledger, Aged Receivable, Aged Payable,
          Cash Flow Statement, Tax Report and Journal Audit (PDF and XLSX export).
        * Asset Management - asset creation, depreciation schedules and disposal.
        * Budget Management - budgets per analytic account and period.
        * Bank statement import and bank reconciliation.
        * PDC (Post-Dated Cheque) management.
        * Customer follow-ups and recurring payments, odoo19 accounting, odoo19 assets, odoo19 pdc, odoo19 full accounting.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['account', 'sale', 'account_check_printing', 'analytic',
                'base_account_budget', 'contacts'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/account_financial_report_data.xml',
        'data/cash_flow_data.xml',
        'data/followup_levels.xml',
        'data/mail_template_followup.xml',
        'data/followup_cron.xml',
        'data/bank_auto_reconcile_cron.xml',
        'data/account_bulk_payment_data.xml',
        'data/account_recurring_invoice_data.xml',
        'data/multiple_invoice_data.xml',
        'data/recurring_entry_cron.xml',
        'data/account_asset_cron.xml',
        'data/account_pdc_data.xml',
        'views/reports_config_view.xml',
        'views/accounting_menu.xml',
        'views/account_group.xml',
        'views/credit_limit_view.xml',
        'views/account_configuration.xml',
        'views/res_config_settings_views.xml',
        'views/account_followup.xml',
        'views/followup_line_views.xml',
        'views/followup_report.xml',
        'wizard/asset_depreciation_confirmation_views.xml',
        'wizard/asset_modify_views.xml',
        'wizard/asset_disposal_views.xml',
        'wizard/asset_revaluation_views.xml',
        'wizard/account_fx_revaluation_views.xml',
        'views/account_asset_asset_views.xml',
        'views/account_asset_category_views.xml',
        'views/account_move_views.xml',
        'views/product_views.xml',
        'views/multiple_invoice_layout_view.xml',
        'views/multiple_invoice_form.xml',
        'views/account_journal_views.xml',
        'views/res_partner_views.xml',
        'wizard/financial_report_views.xml',
        'wizard/account_report_general_ledger_views.xml',
        'wizard/account_report_partner_ledger_views.xml',
        'wizard/kit_account_tax_report_views.xml',
        'wizard/account_balance_report_views.xml',
        'wizard/account_aged_trial_balance_views.xml',
        'wizard/account_print_journal_views.xml',
        'wizard/cash_flow_report_views.xml',
        'wizard/account_bank_book_report_views.xml',
        'wizard/account_cash_book_report_views.xml',
        'wizard/account_day_book_report_views.xml',
        'report/report_financial_template.xml',
        'report/general_ledger_report_template.xml',
        'report/report_journal_audit_template.xml',
        'report/report_aged_partner_template.xml',
        'report/report_trial_balance_template.xml',
        'report/report_tax_template.xml',
        'report/report_partner_ledger_template.xml',
        'report/cash_flow_report_template.xml',
        'report/account_bank_book_template.xml',
        'report/account_cash_book_template.xml',
        'report/account_day_book_template.xml',
        'report/account_asset_report_views.xml',
        'report/report.xml',
        'report/multiple_invoice_layouts.xml',
        'report/multiple_invoice_report_template.xml',
        'report/res_partner_reports.xml',
        'report/res_partner_templates.xml',
        'report/followup_report_templates.xml',
        'report/bulk_payment_report_templates.xml',
        'views/account_recurring_payments_view.xml',
        'views/account_move_line_views.xml',
        'views/account_bank_statement_views.xml',
        'views/account_bank_statement_line_views.xml',
        'views/account_payment_view.xml',
        'views/account_bulk_payment_views.xml',
        'views/account_recurring_invoice_views.xml',
        'wizard/account_lock_date_views.xml',
        'wizard/import_bank_statement_views.xml',
    ],
    'external_dependencies': {
            'python': ['openpyxl', 'ofxparse', 'qifparse', 'xlsxwriter']
        },
    'assets': {
        'web.assets_backend': [
            'base_accounting_kit/static/src/scss/style.scss',
            'base_accounting_kit/static/src/scss/bank_rec_widget.css',
            'base_accounting_kit/static/src/js/bank_reconcile_form_list_widget.js',
            'base_accounting_kit/static/src/js/KanbanController.js',
            'base_accounting_kit/static/src/js/ListController.js',
            'base_accounting_kit/static/src/js/bank_reconcile_form_lines_widget.js',
            'base_accounting_kit/static/src/js/action_manager.js',
            'base_accounting_kit/static/src/xml/bank_rec_widget.xml',
            'base_accounting_kit/static/src/xml/bank_reconcile_widget.xml',
        ]
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': True,
}

