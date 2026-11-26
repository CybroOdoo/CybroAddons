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
from datetime import date, timedelta

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from .common import AccountingKitTestCommon


@tagged('post_install', '-at_install')
class TestPeriodClosing(AccountingKitTestCommon):
    """P2.3-d: Month-end Closing: tasks from templates with activities,
    Done / Undo, the automatic checks, Close (lock) / Reopen, rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.month = date(cls.year - 1, 3, 1)
        cls.month_end = date(cls.year - 1, 3, 31)
        cls.day = date(cls.year - 1, 3, 15)
        roles = {}
        for role, group in (('chief', 'base_accounting_kit.group_account_chief'),
                            ('accountant', 'account.group_account_user')):
            roles[role] = new_test_user(
                cls.env, login='kit_pc_%s' % role, groups='%s,base.group_user' % group,
                company_id=cls.company.id, company_ids=[Command.set(cls.company.ids)])
        cls.users = roles
        Template = cls.env['kit.closing.task.template']
        Template.create([
            {'name': 'Accrue salaries', 'sequence': 1, 'user_id': roles['accountant'].id, 'due_day': 3},
            {'name': 'Review bank charges', 'sequence': 2, 'due_day': 5}])
        cls.expense = cls.kit_account('expense')
        cls.payable = cls.kit_account('liability_payable')
        cls.vendor = cls.env['res.partner'].create({'name': 'Kit PC Vendor'})

    def start(self):
        return self.env['kit.period.closing']._start_month(self.company, self.month)

    def bill(self, ref, amount=100):
        return self.env['account.move'].create({
            'move_type': 'in_invoice', 'partner_id': self.vendor.id, 'ref': ref,
            'invoice_date': self.day, 'date': self.day,
            'invoice_line_ids': [Command.create({'name': 'x', 'quantity': 1, 'price_unit': amount,
                                                 'tax_ids': False})]})

    def test_tasks_and_activities(self):
        """Starting a month copies the templates (due day of the next
        month) and gives the responsible person a To-Do; Done records who
        and when and closes the activity; Undo reopens it."""
        closing = self.start()
        self.assertEqual(closing.name, self.month.strftime('%b %Y'))
        self.assertEqual(closing.date_to, self.month_end)
        salaries, charges = closing.task_ids
        self.assertEqual(salaries.name, 'Accrue salaries')
        self.assertEqual(salaries.date_deadline, date(self.year - 1, 4, 3))
        self.assertEqual(salaries.activity_id.user_id, self.users['accountant'])
        self.assertFalse(charges.activity_id)
        self.assertEqual(closing.progress, 0)
        salaries.with_user(self.users['accountant']).action_done()
        self.assertTrue(salaries.done)
        self.assertEqual(salaries.done_uid, self.users['accountant'])
        self.assertFalse(salaries.activity_id)
        self.assertEqual(closing.progress, 50)
        salaries.action_undo()
        self.assertFalse(salaries.done)
        self.assertTrue(salaries.activity_id)
        extra = self.env['kit.period.closing.task'].create({
            'closing_id': closing.id, 'name': 'One-off', 'user_id': self.users['chief'].id})
        self.assertTrue(extra.activity_id)
        with self.assertRaises(Exception), self.cr.savepoint(), mute_logger('odoo.sql_db'):
            self.env['kit.period.closing']._start_month(self.company, self.month)
            self.env.flush_all()

    def test_checks(self):
        """Each check counts its records: draft entry, unreconciled bank
        transaction, open outstanding payment, negative bank, duplicate
        bills."""
        closing = self.start()
        self.assertFalse(closing.has_warnings or closing.has_blocking)
        self.kit_entry(self.day, [(self.expense, 10, 0), (self.payable, 0, 10)], post=False)
        bank = self.kit_journal('bank')
        self.env['account.bank.statement.line'].create({
            'journal_id': bank.id, 'date': self.day, 'amount': -500, 'payment_ref': 'kit pc fee'})
        self.env['account.payment'].create({
            'payment_type': 'outbound', 'partner_type': 'supplier', 'partner_id': self.vendor.id,
            'amount': 70, 'date': self.day, 'journal_id': bank.id}).action_post()
        self.bill('KIT-DUP-1').action_post()
        self.bill('KIT-DUP-1', 200)
        closing.invalidate_recordset()
        self.assertEqual(closing.draft_count, 2)  # the entry and the second bill
        self.assertEqual(closing.unreconciled_count, 1)
        self.assertEqual(closing.transit_count, 1)
        self.assertAmount(closing.transit_amount, -70)
        self.assertEqual(closing.negative_bank_count, 1)
        self.assertEqual(closing.duplicate_bill_count, 2)
        self.assertTrue(closing.has_blocking and closing.has_warnings)
        action = closing.with_context(check='negative_bank').action_open_check()
        self.assertEqual(action['res_model'], 'account.journal')
        self.assertEqual(self.env['account.journal'].search(action['domain']), bank)
        closing.lock_month = False
        self.assertFalse(closing.has_blocking)

    def test_close_and_reopen(self):
        """Close needs every task done and the warnings accepted; Lock the
        month sets the Global Lock Date; Reopen gives it back (last closed
        month only)."""
        closing = self.start()
        with self.assertRaises(UserError):
            closing.action_close()
        closing.task_ids.action_done()
        self.kit_entry(self.day, [(self.expense, 10, 0), (self.payable, 0, 10)], post=False)
        closing.invalidate_recordset()
        with self.assertRaises(UserError):
            closing.action_close()
        closing.close_anyway = True
        closing.action_close()
        self.assertEqual(closing.state, 'closed')
        self.assertEqual(self.company.fiscalyear_lock_date, self.month_end)
        with self.assertRaises(UserError):
            closing.task_ids[0].action_undo()
        april = self.env['kit.period.closing']._start_month(self.company, date(self.year - 1, 4, 1))
        april.task_ids.action_done()
        april.action_close()
        self.assertEqual(self.company.fiscalyear_lock_date, date(self.year - 1, 4, 30))
        with self.assertRaises(UserError):
            closing.action_reopen()
        april.action_reopen()
        self.assertEqual(self.company.fiscalyear_lock_date, self.month_end)
        closing.action_reopen()
        self.assertFalse(self.company.fiscalyear_lock_date)
        self.assertEqual(closing.state, 'open')

    def test_next_month_and_rights(self):
        """Start Next Month follows the last month; Accountants mark tasks
        done but cannot start or close months nor edit templates."""
        Closing = self.env['kit.period.closing']
        first = Closing.browse(Closing.action_create_next_month()['res_id'])
        today = date.today()
        self.assertEqual(first.date_to.month, (today.month - 2) % 12 + 1)
        second = Closing.browse(Closing.action_create_next_month()['res_id'])
        self.assertEqual(second.date_from, first.date_to + timedelta(days=1))
        accountant = self.users['accountant']
        task = second.task_ids[0].with_user(accountant)
        task.action_done()
        self.assertTrue(task.done)
        with self.assertRaises(UserError):
            Closing.with_user(accountant).action_create_next_month()
        with self.assertRaises(UserError):
            second.with_user(accountant).action_close()
        with self.assertRaises(AccessError):
            self.env['kit.closing.task.template'].with_user(accountant).create({'name': 'x'})
        self.env['kit.period.closing.task'].with_user(accountant).create({'closing_id': second.id, 'name': 'Own task'})
