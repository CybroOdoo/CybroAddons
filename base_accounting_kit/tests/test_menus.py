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
from collections import Counter

from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestMenus(AccountingKitTestCommon):
    """Menus (SP, P2.12): every report menu opens its dynamic screen, the
    Reporting folders follow core's, no duplicate menus, the Review area
    and the Management folders; the old report wizards are gone."""

    def ref(self, xmlid):
        return self.env.ref(xmlid if '.' in xmlid else 'base_accounting_kit.' + xmlid)

    def children(self, folder):
        menus = self.env['ir.ui.menu'].search([('parent_id', '=', self.ref(folder).id)])
        return [m.name for m in menus.sorted(lambda m: (m.sequence, m.id))]

    def test_report_menus_open_dynamic_screens(self):
        """All 13 report menus (12 reports, Aged in two) open the dynamic
        report screen."""
        menus = ['account_day_book_menu', 'account_cash_book_menu', 'account_bank_book_menu', 'menu_tax_report',
                 'menu_print_journal', 'menu_Balance_report', 'menu_general_ledger', 'menu_partner_ledger',
                 'menu_aged_trial_balance', 'menu_aged_payable', 'account_financial_reports_profit_loss',
                 '_account_financial_reports_balance_sheet', 'menu_account_cash_flow_report']
        for xmlid in menus:
            action = self.ref(xmlid).action
            self.assertEqual((action._name, action.tag), ('ir.actions.client', 'kit_dynamic_report'), xmlid)

    def test_reporting_folders(self):
        """Reporting: core's folders plus Audit and Daily Reports, each
        report once, nothing loose; old kit folders removed."""
        self.assertEqual(self.children('account.account_reports_legal_statements_menu'),
                         ['Profit and Loss', 'Balance Sheet', 'Cash Flow Statement'])
        self.assertEqual(self.children('account_reports_audit'),
                         ['General Ledger', 'Trial Balance', 'Journals Audit', 'Bank Reconciliation'])
        self.assertEqual(self.children('account.account_reports_partners_reports_menu'),
                         ['Partner Ledger', 'Aged Receivable', 'Aged Payable'])
        self.assertEqual(self.children('account.account_reports_taxes_and_fiscal_menu'), ['Tax Report'])
        self.assertEqual(self.children('account_reports_daily_reports'), ['Day Book', 'Cash Book', 'Bank Book'])
        loose = self.env['ir.ui.menu'].search([('parent_id', '=', self.ref('account.menu_finance_reports').id),
                                               ('action', '!=', False)])
        self.assertFalse(loose)
        self.assertFalse(self.env.ref('base_accounting_kit.account_reports_generic_statements', raise_if_not_found=False))
        self.assertFalse(self.env.ref('base_accounting_kit.account_reports_partner', raise_if_not_found=False))

    def test_no_duplicate_menus(self):
        """No folder of the Accounting app holds two menus with the same
        name and action."""
        root = self.ref('account.menu_finance')
        menus = self.env['ir.ui.menu'].search([('id', 'child_of', root.id)])
        duplicates = [key for key, count in Counter(
            (m.parent_id.id, m.name, m.action and str(m.action)) for m in menus).items() if count > 1]
        self.assertFalse(duplicates)

    def test_review_and_management(self):
        """Review > To Review (entries to review, drafts, bank
        transactions, open items); Accounting > Bank & Cash (import,
        statements, transactions); Accounting > Management; Configuration > Management;
        Currency Revaluation in Actions for accountants, Lock Dates for
        Chief Accountants."""
        self.assertEqual(self.children('menu_review_to_review'),
                         ['Entries to Review', 'Draft Entries', 'Bank Transactions', 'Open Items'])
        self.assertEqual(self.children('management_menu'), ['Assets', 'Budgets'])
        self.assertEqual(self.children('menu_bank_cash'), ['Import Statement', 'Bank Statements', 'Bank Transactions'])
        self.assertEqual(self.ref('menu_bank_cash').parent_id, self.ref('account.menu_finance_entries'))
        self.assertEqual(self.children('menu_finance_config_assets'),
                         ['Asset Types', 'Budgetary Positions', 'Recurring Templates'])
        draft = self.kit_entry(self.today, [(self.kit_account('expense'), 10, 0), (self.kit_account('asset_current'), 0, 10)],
                               post=False)
        posted = self.kit_entry(self.today, [(self.kit_account('expense'), 20, 0), (self.kit_account('asset_current'), 0, 20)])
        posted.review_state = 'todo'
        to_review = self.env['account.move'].search(safe_eval(self.ref('action_review_entries').domain))
        self.assertIn(posted, to_review)
        self.assertNotIn(draft, to_review)
        self.assertIn("'search_default_unposted': 1", self.ref('action_review_draft_entries').context)
        fx = self.ref('menu_account_fx_revaluation')
        self.assertEqual(fx.parent_id, self.env.ref('account.account_closing_menu'))
        self.assertIn(self.env.ref('account.group_account_user'), fx.group_ids)
        self.assertEqual(self.ref('menu_lock_dates').group_ids, self.ref('group_account_chief'))

    def test_button_icons(self):
        """QA Q5: view buttons use Odoo 20 icon names (Material Symbols); a
        Font Awesome name (icon="fa-...") shows a stray "-" before the icon."""
        ids = self.env['ir.model.data'].search([('module', '=', 'base_accounting_kit'),
                                                ('model', '=', 'ir.ui.view')]).mapped('res_id')
        views = self.env['ir.ui.view'].browse(ids).exists()
        self.assertTrue(views)
        wrong = [view.xml_id for view in views if 'icon="fa-' in (view.arch_db or '')]
        self.assertFalse(wrong)

    def test_old_wizards_removed(self):
        """The report wizards and their PDF actions are gone; only the
        generic dynamic report PDF is left for the reports."""
        for model in ('account.balance.report', 'financial.report', 'cash.flow.report', 'account.day.book.report',
                      'account.cash.book.report', 'account.bank.book.report', 'kit.account.tax.report',
                      'account.print.journal', 'account.common.report', 'account.report.xlsx.mixin'):
            self.assertNotIn(model, self.env)
        for xmlid in ('action_report_trial_balance', 'financial_report_pdf', 'action_report_cash_flow',
                      'action_report_journal', 'action_report_account_tax', 'action_report_bank_book',
                      'action_report_cash_book', 'day_book_pdf_report'):
            self.assertFalse(self.env.ref('base_accounting_kit.' + xmlid, raise_if_not_found=False), xmlid)
        # Leftover journal items list of the old reconciliation widget (removed with its JS in P2.1-c).
        self.assertFalse(self.env.ref('base_accounting_kit.account_move_line_view_tree', raise_if_not_found=False))
