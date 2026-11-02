# -*- coding: utf-8 -*-
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
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged('post_install', '-at_install')
class TestHrExpenseMassPayment(TestExpenseCommon):
    """Posting the journal entries of several expenses and registering their
    payments together."""

    def _approved_expenses(self, count=3):
        """Create employee-paid expenses and approve them, which creates one
        draft journal entry per expense. Amounts differ so that Odoo does
        not ask to confirm duplicates."""
        expenses = self.create_expenses([{
            'name': f'Expense {i}',
            'payment_mode': 'own_account',
            'total_amount_currency': 100.0 * (i + 1),
        } for i in range(count)])
        expenses.action_submit()
        for expense in expenses:
            expense.action_approve()
        return expenses

    def test_post_entries_posts_existing_moves(self):
        """The draft entries created on approval are posted, none added."""
        expenses = self._approved_expenses()
        moves = expenses.account_move_id
        self.assertEqual(len(moves), 3)
        self.assertEqual(set(moves.mapped('state')), {'draft'})
        move_count = self.env['account.move'].search_count([])

        expenses.action_post_entries()

        self.assertEqual(expenses.account_move_id, moves)
        self.assertEqual(set(moves.mapped('state')), {'posted'})
        self.assertEqual(set(expenses.mapped('state')), {'posted'})
        self.assertEqual(self.env['account.move'].search_count([]), move_count)

    def test_post_entries_requires_approved_expenses(self):
        """Nothing is posted when one of the expenses is not approved."""
        approved = self._approved_expenses(count=1)
        draft = self.create_expenses({'name': 'Draft expense'})
        submitted = self.create_expenses({'name': 'Submitted expense'})
        submitted.action_submit()

        for expenses in (draft, submitted, approved | draft):
            with self.assertRaisesRegex(ValidationError, 'approved expenses'):
                expenses.action_post_entries()
        self.assertEqual(approved.account_move_id.state, 'draft')

    def test_post_entries_creates_missing_move(self):
        """An approved expense without a journal entry, e.g. an imported one,
        gets one created and posted."""
        expense = self.create_expenses({'name': 'Imported expense'})
        expense.write({'approval_state': 'approved'})
        self.assertEqual(expense.state, 'approved')
        self.assertFalse(expense.account_move_id)

        expense.action_post_entries()

        self.assertEqual(expense.account_move_id.state, 'posted')
        self.assertEqual(expense.state, 'posted')

    def test_register_payments_together(self):
        """The posted expenses are paid with one registration."""
        expenses = self._approved_expenses()
        expenses.action_post_entries()

        action = expenses.action_pay()
        wizard = self.env[action['res_model']].with_context(
            **action['context']).create({})
        wizard._create_payments()

        self.assertEqual(
            set(expenses.mapped('state')) - {'in_payment', 'paid'}, set())

    def test_list_actions(self):
        """Both actions run from the Actions menu of the expense list."""
        expenses = self._approved_expenses()
        context = {'active_model': 'hr.expense', 'active_ids': expenses.ids}

        self.env.ref(
            'hr_expense_mass_payment.action_post_expense_entries'
        ).with_context(**context).run()
        self.assertEqual(set(expenses.mapped('state')), {'posted'})

        action = self.env.ref(
            'hr_expense_mass_payment.action_expense_mass_payment'
        ).with_context(**context).run()
        self.assertEqual(action['res_model'], 'account.payment.register')
