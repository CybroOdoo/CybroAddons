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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase, tagged


@tagged('analytic_accounts_on_stock_picking', 'account_analytic_line')
class TestAccountAnalyticLine(TransactionCase):
    """Unit tests for the transfer_reference field added to account.analytic.line."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Analytic plan required in Odoo 17+ to create analytic accounts
        cls.analytic_plan = cls.env['account.analytic.plan'].search([], limit=1)
        if not cls.analytic_plan:
            cls.analytic_plan = cls.env['account.analytic.plan'].create({
                'name': 'Test Plan',
            })

        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Test Analytic Account',
            'plan_id': cls.analytic_plan.id,
        })

    def _make_analytic_line(self, transfer_reference=False, **extra):
        """Helper: create a minimal account.analytic.line."""
        vals = {
            'name': 'Test Analytic Line',
            'account_id': self.analytic_account.id,
            'amount': 0.0,
        }
        if transfer_reference:
            vals['transfer_reference'] = transfer_reference
        vals.update(extra)
        return self.env['account.analytic.line'].create(vals)

    # ------------------------------------------------------------------
    # 1. Field existence
    # ------------------------------------------------------------------

    def test_transfer_reference_field_exists(self):
        """transfer_reference field must exist on account.analytic.line."""
        self.assertIn(
            'transfer_reference',
            self.env['account.analytic.line']._fields,
            "Field 'transfer_reference' not found on account.analytic.line",
        )

    def test_transfer_reference_is_char(self):
        """transfer_reference must be a Char field."""
        from odoo.fields import Char
        field = self.env['account.analytic.line']._fields['transfer_reference']
        self.assertIsInstance(field, Char)

    # ------------------------------------------------------------------
    # 2. Default value
    # ------------------------------------------------------------------

    def test_transfer_reference_defaults_to_false(self):
        """A newly created analytic line should have transfer_reference = False."""
        line = self._make_analytic_line()
        self.assertFalse(
            line.transfer_reference,
            "transfer_reference should be False/empty by default",
        )

    # ------------------------------------------------------------------
    # 3. Write a value
    # ------------------------------------------------------------------

    def test_transfer_reference_can_be_set(self):
        """transfer_reference can be set to a non-empty string."""
        line = self._make_analytic_line(transfer_reference='WH/OUT/00001')
        self.assertEqual(line.transfer_reference, 'WH/OUT/00001')

    def test_transfer_reference_write_updates_value(self):
        """write() on an existing record updates transfer_reference correctly."""
        line = self._make_analytic_line()
        line.write({'transfer_reference': 'WH/IN/00042'})
        self.assertEqual(line.transfer_reference, 'WH/IN/00042')

    # ------------------------------------------------------------------
    # 4. Clear the value
    # ------------------------------------------------------------------

    def test_transfer_reference_can_be_cleared(self):
        """transfer_reference can be reset to False after being set."""
        line = self._make_analytic_line(transfer_reference='WH/OUT/00001')
        line.write({'transfer_reference': False})
        self.assertFalse(line.transfer_reference)

    # ------------------------------------------------------------------
    # 5. search() on the field
    # ------------------------------------------------------------------

    def test_search_by_transfer_reference(self):
        """search() must find lines filtered by transfer_reference value."""
        ref = 'WH/OUT/SEARCH_TEST'
        line = self._make_analytic_line(transfer_reference=ref)
        results = self.env['account.analytic.line'].search(
            [('transfer_reference', '=', ref)]
        )
        self.assertIn(line, results)

    def test_search_empty_transfer_reference(self):
        """search() with False domain must find lines without a reference."""
        line = self._make_analytic_line()
        results = self.env['account.analytic.line'].search(
            [('transfer_reference', '=', False)]
        )
        self.assertIn(line, results)

    # ------------------------------------------------------------------
    # 6. Bulk update() — mirrors usage inside account_move.action_post
    # ------------------------------------------------------------------

    def test_bulk_update_transfer_reference(self):
        """update() on a recordset sets transfer_reference on every record."""
        line1 = self._make_analytic_line()
        line2 = self._make_analytic_line()
        batch = line1 | line2
        batch.update({'transfer_reference': 'WH/OUT/BULK'})
        self.assertEqual(line1.transfer_reference, 'WH/OUT/BULK')
        self.assertEqual(line2.transfer_reference, 'WH/OUT/BULK')

    def test_update_does_not_affect_other_lines(self):
        """update() must only affect the targeted recordset, not all lines."""
        unrelated = self._make_analytic_line(transfer_reference='ORIGINAL')
        target = self._make_analytic_line()
        target.update({'transfer_reference': 'CHANGED'})
        # reload unrelated from DB
        unrelated.invalidate_recordset()
        self.assertEqual(unrelated.transfer_reference, 'ORIGINAL')
