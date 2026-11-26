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
from datetime import date

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestClosing(AccountingKitTestCommon):
    """P2.3-a: Accounting > Closing, the five lock dates and lock
    exceptions (core account.lock_exception)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lock = date(cls.year - 2, 6, 30)
        cls.before = date(cls.year - 2, 6, 15)
        cls.expense = cls.kit_account('expense')
        cls.current = cls.kit_account('asset_current')
        cls.chief = new_test_user(
            cls.env, login='kit_closing_chief',
            groups='base_accounting_kit.group_account_chief,base.group_user',
            company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])

    def ref(self, xmlid):
        return self.env.ref(xmlid if '.' in xmlid else 'base_accounting_kit.' + xmlid)

    def wizard(self, user=None, **dates):
        Wizard = self.env['account.lock.date']
        if user:
            Wizard = Wizard.with_user(user).with_context(allowed_company_ids=self.company.ids)
        return Wizard.create(dict(company_id=self.company.id, **dates))

    def entry_date(self):
        """Posting date of an entry dated before the lock date (core moves
        it after the lock date when the period is locked for the user)."""
        self.env['res.company'].invalidate_model()
        return self.kit_entry(self.before, [(self.expense, 10, 0), (self.current, 0, 10)]).date

    def test_five_lock_dates(self):
        """The wizard shows and writes the five core lock dates (Chief
        Accountant); the Hard Lock Date cannot move back."""
        dates = {field: self.lock for field in ('fiscalyear_lock_date', 'tax_lock_date', 'sale_lock_date',
                                                'purchase_lock_date', 'hard_lock_date')}
        self.wizard(user=self.chief, **dates).execute()
        for field, value in dates.items():
            self.assertEqual(self.company[field], value, field)
        self.assertEqual(self.env['account.lock.date'].create({})['hard_lock_date'], self.lock)
        self.assertGreater(self.entry_date(), self.lock)
        with self.assertRaises(UserError):
            self.wizard(hard_lock_date=date(self.year - 3, 1, 31)).execute()
        # unchanged dates are not written again (nothing to check, no error)
        self.wizard(**dates).execute()

    def test_lock_exception(self):
        """An exception lets its user post before the Global Lock Date
        until it is revoked; it is logged with its reason."""
        self.wizard(fiscalyear_lock_date=self.lock).execute()
        self.assertGreater(self.entry_date(), self.lock)
        exception = self.env['account.lock_exception'].create({
            'lock_date_field': 'fiscalyear_lock_date', 'lock_date': False,
            'reason': 'Correct June depreciation'})
        self.assertEqual(exception.company_lock_date, self.lock)
        self.assertEqual(exception.kit_company_lock_date, self.lock)
        self.assertEqual(exception.user_id, self.env.user)
        self.assertEqual(exception.state, 'active')
        self.assertEqual(self.entry_date(), self.before)
        exception.action_revoke()
        self.assertEqual(exception.state, 'revoked')
        self.assertGreater(self.entry_date(), self.lock)
        new = self.env['account.lock_exception'].new({'lock_date_field': 'fiscalyear_lock_date'})
        self.assertEqual(new.kit_company_lock_date, self.lock)
        self.assertEqual(new.display_name, 'New Lock Exception')

    def test_closing_menu_and_rights(self):
        """Lock Dates, Lock Exceptions and Currency Revaluation are under
        core's Accounting > Closing; the old Actions folder is gone;
        exceptions are created and revoked by Administrators only."""
        closing = self.ref('account.account_closing_menu')
        for xmlid in ('menu_lock_dates', 'menu_kit_lock_exceptions', 'menu_account_fx_revaluation'):
            self.assertEqual(self.ref(xmlid).parent_id, closing, xmlid)
        self.assertFalse(self.env.ref('base_accounting_kit.actions_menu', raise_if_not_found=False))
        action = self.ref('action_kit_lock_exceptions')
        self.assertEqual(action.view_ids.mapped('view_id'),
                         self.ref('view_kit_lock_exception_list') | self.ref('view_kit_lock_exception_form'))
        Exceptions = self.env['account.lock_exception'].with_user(self.chief)
        Exceptions.search([])  # may read
        with self.assertRaises(AccessError):
            Exceptions.create({'lock_date_field': 'sale_lock_date', 'lock_date': False, 'reason': 'x'})
