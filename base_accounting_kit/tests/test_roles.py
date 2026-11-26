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
import base64

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from .common import AccountingKitTestCommon

ROLES = {
    'readonly': 'account.group_account_readonly',
    'invoicing': 'account.group_account_invoice',
    'accountant': 'account.group_account_user',
    'chief': 'base_accounting_kit.group_account_chief',
    'administrator': 'account.group_account_manager',
}
REPORT_MENUS = ['menu_Balance_report', 'menu_general_ledger', 'menu_print_journal', 'menu_bank_reconciliation_report',
                'menu_partner_ledger', 'menu_aged_trial_balance', 'menu_aged_payable', 'menu_tax_report',
                'account_financial_reports_profit_loss', '_account_financial_reports_balance_sheet',
                'menu_account_cash_flow_report', 'account_day_book_menu', 'account_cash_book_menu',
                'account_bank_book_menu']
REPORTS = ['trial_balance', 'general_ledger', 'partner_ledger', 'aged', 'financial', 'cash_flow', 'day_book',
           'cash_book', 'bank_book', 'tax', 'journal_audit', 'bank_reconciliation']


@tagged('post_install', '-at_install')
class TestRoles(AccountingKitTestCommon):
    """What each accounting role (Read-only, Invoicing, Accountant, Chief
    Accountant, Administrator) sees and may do in the kit's menus and
    features."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = {role: new_test_user(
            cls.env, login='kit_role_%s' % role, groups='%s,base.group_user' % group,
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
            for role, group in ROLES.items()}
        cls.bank = cls.company_data['default_journal_bank']
        cls.misc = cls.company_data['default_journal_misc']
        cls.expense = cls.company_data['default_account_expense']

    def as_role(self, role, model):
        return self.env[model].with_user(self.users[role]).with_context(allowed_company_ids=self.company.ids)

    def visible(self, role, xmlid):
        """The menu shows: its groups and those of all its parents."""
        Menu = self.env['ir.ui.menu'].with_user(self.users[role])
        visible = set(Menu._visible_menu_ids())
        menu = self.env.ref(xmlid if '.' in xmlid else 'base_accounting_kit.' + xmlid)
        return all(int(i) in visible for i in menu.parent_path.strip('/').split('/'))

    def import_csv(self, role):
        csv = "date,label,amount\n2026-03-01,Role %s,10\n" % role
        return self.as_role(role, 'import.bank.statement').create({
            'attachment': base64.b64encode(csv.encode()).decode(), 'file_name': '%s.csv' % role,
            'journal_id': self.bank.id}).action_statement_import()

    def statement_list_can_create(self, role):
        arch = self.as_role(role, 'account.bank.statement').get_view(
            self.env.ref('account.view_bank_statement_tree').id, 'list')['arch']
        return 'create="false"' not in arch.lower()

    def lock(self, role):
        self.as_role(role, 'account.lock.date').create({
            'company_id': self.company.id, 'sale_lock_date': '2020-01-31'}).execute()

    def test_reports_for_every_role_with_reports(self):
        """Read-only users see and open all report menus (incl. P&L,
        Balance Sheet, Cash Flow, General Ledger, Tax Report); Invoicing
        users do not get the financial statements."""
        for xmlid in REPORT_MENUS:
            self.assertTrue(self.visible('readonly', xmlid), xmlid)
            self.assertTrue(self.visible('accountant', xmlid), xmlid)
        pl = self.env.ref('base_accounting_kit.account_financial_report_profitandloss0')
        for name in REPORTS:
            options = {'account_report_id': pl.id} if name == 'financial' else {}
            self.assertTrue(self.as_role('readonly', 'account.dynamic.report.' + name).get_report(options)['lines']
                            is not None, name)
        self.assertFalse(self.visible('invoicing', 'account_financial_reports_profit_loss'))

    def test_read_only(self):
        """Read-only: no import, no statement creation from the list, no
        reconciliation, no assets, no lock dates."""
        self.assertFalse(self.statement_list_can_create('readonly'))
        self.assertTrue(self.visible('readonly', 'menu_bank_cash_statements'))
        self.assertFalse(self.visible('readonly', 'menu_bank_cash_import'))
        with self.assertRaises(AccessError):
            self.import_csv('readonly')
        self.assertFalse(self.as_role('readonly', 'account.asset.asset').has_access('create'))
        self.assertFalse(self.as_role('readonly', 'account.bank.statement.line').has_access('write'))
        with self.assertRaises(AccessError):
            self.lock('readonly')

    def test_invoicing(self):
        """Invoicing: no statement import (core lets them only read
        statements), no import formats, no assets to confirm, no lock dates."""
        self.assertFalse(self.visible('invoicing', 'menu_bank_cash_import'))
        self.assertFalse(self.statement_list_can_create('invoicing'))
        self.assertFalse(self.as_role('invoicing', 'kit.statement.import.map').has_access('create'))
        kanban = self.as_role('invoicing', 'account.journal').get_view(
            self.env.ref('account.account_journal_dashboard_kanban_view').id, 'kanban')['arch']
        self.assertNotIn('action_import_wizard', kanban)
        with self.assertRaises(AccessError):
            self.import_csv('invoicing')
        self.assertFalse(self.as_role('invoicing', 'account.asset.category').has_access('create'))

    def test_accountant(self):
        """Accountant: imports statements, creates statements from the list,
        saves import formats; lock dates stay with the Chief Accountant."""
        self.assertTrue(self.visible('accountant', 'menu_bank_cash_import'))
        self.assertTrue(self.statement_list_can_create('accountant'))
        self.import_csv('accountant')
        self.assertTrue(self.as_role('accountant', 'kit.statement.import.map').has_access('create'))
        self.assertTrue(self.as_role('accountant', 'account.asset.asset').has_access('create'))
        self.assertFalse(self.as_role('accountant', 'account.asset.category').has_access('create'))
        self.assertFalse(self.visible('accountant', 'menu_lock_dates'))
        with self.assertRaises(UserError):
            self.lock('accountant')

    def test_chief_and_administrator(self):
        """Chief Accountant: Lock Dates in the menu and allowed; asset
        types. Administrator: the same, plus the Configuration menus."""
        for role in ('chief', 'administrator'):
            self.assertTrue(self.visible(role, 'menu_lock_dates'), role)
            self.lock(role)
            self.assertEqual(str(self.company.sale_lock_date), '2020-01-31')
            self.company.sudo().sale_lock_date = False
            self.assertTrue(self.as_role(role, 'account.asset.category').has_access('create'), role)
        self.assertFalse(self.visible('chief', 'menu_kit_statement_import_map'))
        self.assertTrue(self.visible('administrator', 'menu_kit_statement_import_map'))
