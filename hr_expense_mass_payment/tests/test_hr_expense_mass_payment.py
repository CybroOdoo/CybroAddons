# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrExpenseMassPayment(TransactionCase):
    """Test suite for the hr_expense_mass_payment module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Travel Expense',
            'can_be_expensed': True,
            'standard_price': 0.0,

        })

        cls.expense_account = cls.env['account.account'].search(
            [('account_type', '=', 'expense')], limit=1
        )

    def _make_expense(self, name='Test Expense', total_amount=500.0,
                      set_account=True):
        """Create and return a draft hr.expense."""
        vals = {
            'name': name,
            'employee_id': self.employee.id,
            'product_id': self.product.id,
            'total_amount': total_amount,
        }
        if set_account and self.expense_account:
            vals['account_id'] = self.expense_account.id
        return self.env['hr.expense'].create(vals)

    def _set_approved(self, expense):
        """Force an expense into 'approved' state.

        In Odoo 19 there is no hr.expense.sheet model; the approval lifecycle
        lives entirely on hr.expense.  For unit tests we bypass the interactive
        workflow (manager confirmation, email, etc.) and write the state
        directly – the standard pattern used in Odoo's own test suite.
        """
        expense.write({'state': 'approved'})

    def test_action_post_entries_raises_for_draft_expense(self):
        """action_post_entries must raise ValidationError for a draft expense."""
        expense = self._make_expense('Draft Expense')
        self.assertEqual(expense.state, 'draft')
        with self.assertRaises(ValidationError):
            expense.action_post_entries()

    def test_action_post_entries_raises_for_submitted_expense(self):
        """action_post_entries must raise ValidationError when state is
        'submitted' (not yet approved)."""
        expense = self._make_expense('Submitted Expense')
        expense.write({'state': 'submitted'})
        with self.assertRaises(ValidationError):
            expense.action_post_entries()

    def test_action_post_entries_raises_for_mixed_states(self):
        """action_post_entries must raise ValidationError when even one
        expense in the recordset is not approved."""
        approved_exp = self._make_expense('Approved', 200.0)
        self._set_approved(approved_exp)

        draft_exp = self._make_expense('Draft', 100.0)

        with self.assertRaises(ValidationError):
            (approved_exp | draft_exp).action_post_entries()

    def test_action_post_entries_error_message_mentions_approved(self):
        """The ValidationError message should mention 'approved'."""
        expense = self._make_expense('Bad State')
        try:
            expense.action_post_entries()
            self.fail('Expected ValidationError was not raised')
        except ValidationError as e:
            self.assertIn('approved', str(e).lower())

    def test_action_post_entries_auto_assigns_account_when_missing(self):
        """When an approved expense has no account_id, action_post_entries
        should automatically assign an expense-type account."""
        expense = self._make_expense('No Account', set_account=False)
        # The product may auto-populate account_id via its expense account
        # configuration; force-clear it so the pre-condition is guaranteed.
        expense.write({'account_id': False})
        self._set_approved(expense)
        self.assertFalse(expense.account_id,
                         "Pre-condition: account_id should be empty")

        expense.action_post_entries()

        self.assertTrue(expense.account_id,
                        "account_id should be set after action_post_entries")
        self.assertEqual(
            expense.account_id.account_type,
            'expense',
            "Auto-assigned account should be of type 'expense'",
        )

    def test_action_post_entries_preserves_existing_account(self):
        """action_post_entries must not overwrite an account_id that is
        already set on the expense."""
        expense = self._make_expense('Has Account', set_account=True)
        self._set_approved(expense)
        original_account = expense.account_id
        self.assertTrue(original_account,
                        "Pre-condition: account_id must already be set")

        expense.action_post_entries()

        self.assertEqual(
            expense.account_id, original_account,
            "account_id should remain unchanged after action_post_entries",
        )

    def test_action_post_entries_single_approved_expense(self):
        """action_post_entries completes without error for one approved
        expense that already has an account_id."""
        expense = self._make_expense('Single Approved', 300.0)
        self._set_approved(expense)
        self.assertEqual(expense.state, 'approved')

        expense.action_post_entries()

    def test_action_post_entries_multiple_approved_expenses(self):
        """action_post_entries handles a recordset of multiple approved
        expenses without error – the core mass-payment scenario."""
        exp1 = self._make_expense('Mass Expense 1', 100.0)
        exp2 = self._make_expense('Mass Expense 2', 250.0)
        exp3 = self._make_expense('Mass Expense 3', 75.0)

        for exp in (exp1, exp2, exp3):
            self._set_approved(exp)

        all_approved = exp1 | exp2 | exp3
        self.assertTrue(
            all(e.state == 'approved' for e in all_approved),
            "Pre-condition: all three expenses must be in 'approved' state",
        )

        all_approved.action_post_entries()

    def test_action_post_entries_mass_payment_count(self):
        """Each expense in the mass recordset is processed individually –
        the loop in action_post_entries iterates over all records."""
        expenses = self.env['hr.expense']
        for i in range(3):
            exp = self._make_expense(f'Bulk Expense {i}', 50.0 * (i + 1))
            self._set_approved(exp)
            expenses |= exp

        # All three must remain approved before the call
        self.assertEqual(len(expenses), 3)
        # Should not raise
        expenses.action_post_entries()

    def test_action_post_entries_state_does_not_revert_to_draft(self):
        """After action_post_entries, the expense must not revert to draft."""
        expense = self._make_expense('Post State Check', set_account=False)
        expense.write({'account_id': False})
        self._set_approved(expense)

        expense.action_post_entries()

        self.assertNotEqual(
            expense.state, 'draft',
            "Expense should not revert to draft after posting",
        )
