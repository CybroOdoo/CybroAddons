# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


_CONFIG_PARAM = 'cancel_landed_cost_odoo.land_cost_cancel_modes'


def _set_cancel_mode(env, mode):
    """Helper — write the cancel mode directly to ir.config_parameter."""
    env['ir.config_parameter'].sudo().set_param(_CONFIG_PARAM, mode)


@tagged('post_install', '-at_install')
class TestStockLandedCostFields(TransactionCase):
    """TC-11 to TC-14 — Field definition tests for StockLandedCost.
    Source: cancel_landed_cost_odoo/models/stock_landed_cost.py
    """

    # -----------------------------------------------------------------------
    # Field existence & type  (TC-11 – TC-14)
    # -----------------------------------------------------------------------

    def test_11_is_cancel_field_exists_on_stock_landed_cost(self):
        """TC-11: 'is_cancel' Boolean field must be present on
        stock.landed.cost."""
        self.assertIn(
            'is_cancel',
            self.env['stock.landed.cost']._fields,
            "Field 'is_cancel' must exist on stock.landed.cost",
        )

    def test_12_is_cancel_field_is_boolean(self):
        """TC-12: 'is_cancel' must be declared as a fields.Boolean."""
        field = self.env['stock.landed.cost']._fields.get('is_cancel')
        self.assertIsNotNone(field)
        self.assertIsInstance(
            field, fields.Boolean,
            "'is_cancel' must be a Boolean field",
        )


    def test_13_is_cancel_defaults_to_false(self):
        """TC-13: 'is_cancel' must default to False on a new landed cost."""
        lc = self.env['stock.landed.cost'].create({'vendor_bill_id': False})
        self.assertFalse(
            lc.is_cancel,
            "'is_cancel' must default to False on a newly created landed cost",
        )


@tagged('post_install', '-at_install')
class TestStockLandedCostActions(TransactionCase):
    """TC-15 to TC-40 — Functional tests for all cancel/reset/delete methods.
    """

    def setUp(self):
        super().setUp()
        _set_cancel_mode(self.env, 'cancel')

        # ── Company & accounts ────────────────────────────────────────────
        self.company = self.env.company
        self.currency = self.company.currency_id

        # ── Partner ───────────────────────────────────────────────────────
        self.partner = self.env['res.partner'].create({'name': 'LC Test Vendor'})

        # ── Product category with AVCO costing + automated valuation ─────
        #    Landed costs require FIFO or Average costing (not Standard) and
        #    real_time valuation so that account_move_id is created on validate.
        #    The category also needs a stock journal + valuation account; without
        #    them button_validate() succeeds but skips journal entry creation.
        stock_journal = (
            self.company.account_stock_journal_id
            or self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.company.id),
            ], limit=1)
        )
        stock_valuation_account = (
            self.company.account_stock_valuation_id
            or self.env['account.account'].search([
                ('account_type', 'in', ['asset_current', 'asset_non_current', 'asset_fixed']),
                ('company_id', '=', self.company.id),
                ('deprecated', '=', False),
            ], limit=1)
        )
        self.product_categ = self.env['product.category'].create({
            'name': 'LC Test Category (FIFO)',
            'property_cost_method': 'fifo',
            'property_valuation': 'real_time',
            'property_stock_journal': stock_journal.id if stock_journal else False,
            'property_stock_valuation_account_id': stock_valuation_account.id if stock_valuation_account else False,
        })

        # ── Product (storable, AVCO) ──────────────────────────────────────
        #    In Odoo 19, storable products use type='consu' + is_storable=True.
        #    The old type='product' value was removed; 'product' is now only
        #    represented by the is_storable boolean on the stock module extension.
        self.product = self.env['product.product'].create({
            'name': 'LC Test Product',
            'type': 'consu',
            'is_storable': True,
            'standard_price': 100.0,
            'categ_id': self.product_categ.id,
        })

        # ── Service product for landed cost line ──────────────────────────
        self.lc_product = self.env['product.product'].search(
            [('landed_cost_ok', '=', True)], limit=1
        )
        if not self.lc_product:
            # Create a minimal service product that can be used on landed costs
            lc_account = self.env['account.account'].search([
                ('account_type', 'in', ['expense', 'expense_direct_cost']),
                ('company_id', '=', self.company.id),
            ], limit=1)
            self.lc_product = self.env['product.product'].create({
                'name': 'LC Service Product',
                'type': 'service',
                'landed_cost_ok': True,
                'property_account_expense_id': lc_account.id if lc_account else False,
            })

        # ── Warehouse / locations ─────────────────────────────────────────
        self.wh = self.env.ref('stock.warehouse0')
        self.loc_supplier = self.env.ref('stock.stock_location_suppliers')
        self.loc_stock = self.env.ref('stock.stock_location_stock')

    def _make_validated_landed_cost(self):
        """Create and validate a landed cost record so it is in 'done' state
        with an associated account_move_id, ready for cancellation tests."""
        # -- receipt picking --------------------------------------------------
        picking_type_in = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.wh.id),
            ('code', '=', 'incoming'),
        ], limit=1)
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': picking_type_in.id,
            'location_id': self.loc_supplier.id,
            'location_dest_id': self.loc_stock.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 5,
                'location_id': self.loc_supplier.id,
                'location_dest_id': self.loc_stock.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()
        for ml in picking.move_line_ids:
            ml.quantity = ml.move_id.product_uom_qty
            ml.picked = True
        picking.button_validate()

        # -- landed cost ------------------------------------------------------
        lc = self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'cost_lines': [(0, 0, {
                'product_id': self.lc_product.id,
                'price_unit': 50.0,
                'split_method': 'equal',
            })],
        })
        lc.button_validate()
        return lc

    def _make_draft_landed_cost(self):
        """Return a landed cost still in draft (not yet validated)."""
        picking_type_in = self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.wh.id),
            ('code', '=', 'incoming'),
        ], limit=1)
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': picking_type_in.id,
            'location_id': self.loc_supplier.id,
            'location_dest_id': self.loc_stock.id,
            'move_ids': [(0, 0, {
                'product_id': self.product.id,
                'product_uom': self.product.uom_id.id,
                'product_uom_qty': 3,
                'location_id': self.loc_supplier.id,
                'location_dest_id': self.loc_stock.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()
        for ml in picking.move_line_ids:
            ml.quantity = ml.move_id.product_uom_qty
            ml.picked = True
        picking.button_validate()

        return self.env['stock.landed.cost'].create({
            'picking_ids': [(4, picking.id)],
            'cost_lines': [(0, 0, {
                'product_id': self.lc_product.id,
                'price_unit': 30.0,
                'split_method': 'equal',
            })],
        })

    # -----------------------------------------------------------------------
    # _revert_landed_cost()  (TC-15 – TC-18)
    # -----------------------------------------------------------------------

    def test_15_revert_removes_account_move(self):
        """TC-15: _revert_landed_cost() must delete the associated journal
        entry (account_move_id) from a validated landed cost."""
        lc = self._make_validated_landed_cost()
        self.assertTrue(lc.account_move_id, "Landed cost must have a journal entry after validation")
        lc._revert_landed_cost()
        self.assertFalse(
            lc.account_move_id,
            "_revert_landed_cost() must remove the account_move_id",
        )


    def test_16_revert_clears_valuation_adjustment_lines(self):
        """TC-16: _revert_landed_cost() must unlink all
        valuation_adjustment_lines of the landed cost."""
        lc = self._make_validated_landed_cost()
        self.assertTrue(
            lc.valuation_adjustment_lines,
            "Landed cost must have valuation_adjustment_lines after validation",
        )
        lc._revert_landed_cost()
        self.assertFalse(
            lc.valuation_adjustment_lines,
            "_revert_landed_cost() must remove all valuation_adjustment_lines",
        )

    def test_17_revert_on_draft_landed_cost_does_not_raise(self):
        """TC-17: _revert_landed_cost() called on a draft (unvalidated) landed
        cost must not raise an exception — it should be a no-op gracefully."""
        lc = self._make_draft_landed_cost()
        try:
            lc._revert_landed_cost()
        except Exception as exc:
            self.fail(
                f"_revert_landed_cost() raised an exception on a draft "
                f"landed cost: {exc}"
            )

    def test_18_revert_idempotent_when_called_twice(self):
        """TC-18: Calling _revert_landed_cost() twice in sequence must not
        raise — idempotency guard (second call finds nothing to revert)."""
        lc = self._make_validated_landed_cost()
        lc._revert_landed_cost()
        try:
            lc._revert_landed_cost()
        except Exception as exc:
            self.fail(
                f"Second call to _revert_landed_cost() raised: {exc}"
            )

    # -----------------------------------------------------------------------
    # action_landed_cost_cancel()  (TC-19 – TC-22)
    # -----------------------------------------------------------------------

    def test_19_action_cancel_sets_state_to_cancel(self):
        """TC-19: action_landed_cost_cancel() must set the landed cost state
        to 'cancel'."""
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_cancel()
        self.assertEqual(
            lc.state, 'cancel',
            "State must be 'cancel' after action_landed_cost_cancel()",
        )


    def test_20_action_cancel_sets_is_cancel_true(self):
        """TC-20: action_landed_cost_cancel() must set is_cancel=True on the
        landed cost record."""
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_cancel()
        self.assertTrue(
            lc.is_cancel,
            "is_cancel must be True after action_landed_cost_cancel()",
        )


    def test_21_action_cancel_removes_journal_entry(self):
        """TC-21: action_landed_cost_cancel() must remove the associated
        journal entry via _revert_landed_cost()."""
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_cancel()
        self.assertFalse(
            lc.account_move_id,
            "account_move_id must be removed after action_landed_cost_cancel()",
        )


    def test_22_action_cancel_on_multiple_records(self):
        """TC-22: action_landed_cost_cancel() must process all records in a
        recordset (bulk cancel from tree view)."""
        lc1 = self._make_validated_landed_cost()
        lc2 = self._make_validated_landed_cost()
        combined = lc1 | lc2
        combined.action_landed_cost_cancel()
        for lc in combined:
            self.assertEqual(lc.state, 'cancel')
            self.assertTrue(lc.is_cancel)


    # -----------------------------------------------------------------------
    # action_landed_cost_reset_and_cancel()  (TC-23 – TC-26)
    # -----------------------------------------------------------------------

    def test_23_reset_and_cancel_sets_state_to_draft(self):
        """TC-23: action_landed_cost_reset_and_cancel() must set the landed
        cost state to 'draft'."""
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_reset_and_cancel()
        self.assertEqual(
            lc.state, 'draft',
            "State must be 'draft' after action_landed_cost_reset_and_cancel()",
        )


    def test_24_reset_and_cancel_sets_is_cancel_false(self):
        """TC-24: action_landed_cost_reset_and_cancel() must set is_cancel=False
        so the Cancel button becomes visible again."""
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_reset_and_cancel()
        self.assertFalse(
            lc.is_cancel,
            "is_cancel must be False after action_landed_cost_reset_and_cancel()",
        )


    def test_25_reset_and_cancel_removes_journal_entry(self):
        """TC-25: action_landed_cost_reset_and_cancel() must remove the
        associated journal entry."""
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_reset_and_cancel()
        self.assertFalse(
            lc.account_move_id,
            "account_move_id must be removed after reset_and_cancel()",
        )


    def test_26_reset_and_cancel_on_multiple_records(self):
        """TC-26: action_landed_cost_reset_and_cancel() must process all
        records in a recordset (bulk reset from tree view)."""
        lc1 = self._make_validated_landed_cost()
        lc2 = self._make_validated_landed_cost()
        combined = lc1 | lc2
        combined.action_landed_cost_reset_and_cancel()
        for lc in combined:
            self.assertEqual(lc.state, 'draft')
            self.assertFalse(lc.is_cancel)


    # -----------------------------------------------------------------------
    # action_landed_cost_cancel_and_delete()  (TC-27 – TC-30)
    # -----------------------------------------------------------------------

    def test_27_cancel_and_delete_removes_record(self):
        """TC-27: action_landed_cost_cancel_and_delete() must delete the landed
        cost record from the database."""
        lc = self._make_validated_landed_cost()
        lc_id = lc.id
        lc.action_landed_cost_cancel_and_delete()
        remaining = self.env['stock.landed.cost'].search([('id', '=', lc_id)])
        self.assertFalse(
            remaining,
            "Landed cost record must not exist after action_landed_cost_cancel_and_delete()",
        )

    def test_28_cancel_and_delete_removes_journal_entry(self):
        """TC-28: action_landed_cost_cancel_and_delete() must remove the
        journal entry before deleting the record."""
        lc = self._make_validated_landed_cost()
        move_id = lc.account_move_id.id
        lc.action_landed_cost_cancel_and_delete()
        move = self.env['account.move'].search([('id', '=', move_id)])
        self.assertFalse(
            move,
            "Journal entry must be deleted by action_landed_cost_cancel_and_delete()",
        )


    def test_29_cancel_and_delete_on_multiple_records(self):
        """TC-29: action_landed_cost_cancel_and_delete() must delete ALL
        records in a recordset (bulk delete from tree view)."""
        lc1 = self._make_validated_landed_cost()
        lc2 = self._make_validated_landed_cost()
        ids = [lc1.id, lc2.id]
        (lc1 | lc2).action_landed_cost_cancel_and_delete()
        remaining = self.env['stock.landed.cost'].search([('id', 'in', ids)])
        self.assertFalse(
            remaining,
            "All landed cost records must be deleted in bulk cancel_and_delete",
        )


    def test_30_cancel_and_delete_on_draft_does_not_raise(self):
        """TC-30: action_landed_cost_cancel_and_delete() on a draft landed
        cost (no journal entry) must complete without error."""
        lc = self._make_draft_landed_cost()
        lc_id = lc.id
        try:
            lc.action_landed_cost_cancel_and_delete()
        except Exception as exc:
            self.fail(
                f"action_landed_cost_cancel_and_delete() raised on draft: {exc}"
            )
        remaining = self.env['stock.landed.cost'].search([('id', '=', lc_id)])
        self.assertFalse(remaining, "Draft record must also be deleted")

    # -----------------------------------------------------------------------
    # action_landed_cost_cancel_form() — 'cancel' mode  (TC-31 – TC-33)
    # -----------------------------------------------------------------------

    def test_31_form_cancel_mode_sets_state_to_cancel(self):
        """TC-31: When cancel mode is 'cancel', action_landed_cost_cancel_form()
        must set state='cancel' and is_cancel=True."""
        _set_cancel_mode(self.env, 'cancel')
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_cancel_form()
        self.assertEqual(lc.state, 'cancel')
        self.assertTrue(lc.is_cancel)


    def test_32_form_cancel_mode_removes_journal_entry(self):
        """TC-32: When cancel mode is 'cancel', action_landed_cost_cancel_form()
        must remove the journal entry via _revert_landed_cost()."""
        _set_cancel_mode(self.env, 'cancel')
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_cancel_form()
        self.assertFalse(
            lc.account_move_id,
            "account_move_id must be removed when form cancel mode is 'cancel'",
        )


    def test_33_form_cancel_mode_record_still_exists(self):
        """TC-33: When cancel mode is 'cancel', the landed cost record must
        NOT be deleted — it stays in 'cancel' state."""
        _set_cancel_mode(self.env, 'cancel')
        lc = self._make_validated_landed_cost()
        lc_id = lc.id
        lc.action_landed_cost_cancel_form()
        self.assertTrue(
            self.env['stock.landed.cost'].search([('id', '=', lc_id)]),
            "Record must still exist after form cancel with mode='cancel'",
        )


    # -----------------------------------------------------------------------
    # action_landed_cost_cancel_form() — 'cancel_draft' mode  (TC-34 – TC-36)
    # -----------------------------------------------------------------------

    def test_34_form_cancel_draft_mode_sets_state_to_draft(self):
        """TC-34: When cancel mode is 'cancel_draft', action_landed_cost_cancel_form()
        must set state='draft'."""
        _set_cancel_mode(self.env, 'cancel_draft')
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_cancel_form()
        self.assertEqual(
            lc.state, 'draft',
            "State must be 'draft' when form cancel mode is 'cancel_draft'",
        )


    def test_35_form_cancel_draft_mode_sets_is_cancel_false(self):
        """TC-35: When cancel mode is 'cancel_draft', is_cancel must be False
        so the Cancel button is re-shown."""
        _set_cancel_mode(self.env, 'cancel_draft')
        lc = self._make_validated_landed_cost()
        lc.action_landed_cost_cancel_form()
        self.assertFalse(
            lc.is_cancel,
            "is_cancel must be False when form cancel mode is 'cancel_draft'",
        )


    def test_36_form_cancel_draft_mode_record_still_exists(self):
        """TC-36: When cancel mode is 'cancel_draft', the landed cost record
        must NOT be deleted — it returns to draft."""
        _set_cancel_mode(self.env, 'cancel_draft')
        lc = self._make_validated_landed_cost()
        lc_id = lc.id
        lc.action_landed_cost_cancel_form()
        self.assertTrue(
            self.env['stock.landed.cost'].search([('id', '=', lc_id)]),
            "Record must still exist after form cancel with mode='cancel_draft'",
        )

    # -----------------------------------------------------------------------
    # action_landed_cost_cancel_form() — 'cancel_delete' mode
    # -----------------------------------------------------------------------

    def test_37_form_cancel_delete_mode_deletes_record(self):
        """TC-37: When cancel mode is 'cancel_delete',
        action_landed_cost_cancel_form() must delete the landed cost record."""
        _set_cancel_mode(self.env, 'cancel_delete')
        lc = self._make_validated_landed_cost()
        lc_id = lc.id
        lc.action_landed_cost_cancel_form()
        remaining = self.env['stock.landed.cost'].search([('id', '=', lc_id)])
        self.assertFalse(
            remaining,
            "Record must be deleted when form cancel mode is 'cancel_delete'",
        )

    def test_38_form_cancel_delete_mode_removes_journal_entry(self):
        """TC-38: When cancel mode is 'cancel_delete', the journal entry must
        be removed before the record is deleted."""
        _set_cancel_mode(self.env, 'cancel_delete')
        lc = self._make_validated_landed_cost()
        move_id = lc.account_move_id.id
        lc.action_landed_cost_cancel_form()
        move = self.env['account.move'].search([('id', '=', move_id)])
        self.assertFalse(
            move,
            "Journal entry must be removed in 'cancel_delete' form mode",
        )

    def test_39_form_cancel_delete_mode_returns_reload_action(self):
        """TC-39: When cancel mode is 'cancel_delete',
        action_landed_cost_cancel_form() must return an 'ir.actions.client'
        action with tag='reload' to redirect the UI to the list view."""
        _set_cancel_mode(self.env, 'cancel_delete')
        lc = self._make_validated_landed_cost()
        result = lc.action_landed_cost_cancel_form()
        self.assertIsInstance(result, dict, "Return value must be a dict")
        self.assertEqual(
            result.get('type'), 'ir.actions.client',
            "Return type must be 'ir.actions.client'",
        )
        self.assertEqual(
            result.get('tag'), 'reload',
            "Action tag must be 'reload'",
        )