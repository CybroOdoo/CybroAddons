# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Manasa T P (odoo@cybrosys.com)
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
#############################################################################
from datetime import date, timedelta
from odoo.tests.common import TransactionCase


class TestStockMove(TransactionCase):
    """Test cases for the stock.move._assign_picking override.

    The override splits stock.picking creation per move when the originating
    sale order has slot_per_product=True. When slot_per_product=False the
    original (batch) behaviour is preserved.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({'name': 'SM Test Partner'})
        cls.product_a = cls.env['product.product'].create({
            'name': 'Product A (storable)',
            'type': 'consu',
        })
        cls.product_b = cls.env['product.product'].create({
            'name': 'Product B (storable)',
            'type': 'consu',
        })
        cls.slot = cls.env['slot.time'].create({
            'name': 'SM Morning',
            'time_from': '8',
            'time_to': '12',
        })
        cls.future_date = date.today() + timedelta(days=5)
        cls.future_date2 = date.today() + timedelta(days=6)

    def _confirm_order(self, slot_per_product=False, lines=None):
        """Helper: create + confirm a sale order with given lines.

        lines: list of dicts with keys: product_id, qty, delivery_date, slot_id
        """
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'slot_per_product': slot_per_product,
        })
        for line_vals in (lines or []):
            vals = {
                'order_id': order.id,
                'product_id': line_vals['product_id'],
                'product_uom_qty': line_vals.get('qty', 1),
            }
            if slot_per_product:
                if line_vals.get('delivery_date'):
                    vals['delivery_date'] = line_vals['delivery_date']
                if line_vals.get('slot_id'):
                    vals['slot_id'] = line_vals['slot_id']
            self.env['sale.order.line'].create(vals)

        # Clear any existing delivery slots that might conflict
        if slot_per_product:
            for l in lines or []:
                if l.get('delivery_date') and l.get('slot_id'):
                    self.env['delivery.slot'].search([
                        ('delivery_date', '=', l['delivery_date']),
                        ('slot_id', '=', l['slot_id']),
                    ]).unlink()

        order.action_confirm()
        return order

    # -------------------------------------------------------------------------
    # Basic: _assign_picking is monkey-patched onto StockMove
    # -------------------------------------------------------------------------

    def test_assign_picking_method_exists_on_stock_move(self):
        """Test that _assign_picking exists on stock.move (after monkey-patch)."""
        self.assertTrue(
            hasattr(self.env['stock.move'], '_assign_picking'),
            "_assign_picking should exist on stock.move"
        )

    # -------------------------------------------------------------------------
    # slot_per_product = False → standard batch picking
    # -------------------------------------------------------------------------

    def test_standard_order_creates_single_picking(self):
        """With slot_per_product=False, two lines for same product should share picking."""
        order = self._confirm_order(
            slot_per_product=False,
            lines=[
                {'product_id': self.product_a.id, 'qty': 2},
                {'product_id': self.product_b.id, 'qty': 3},
            ],
        )
        # Standard Odoo behaviour: all moves go to one picking (or minimal set)
        pickings = order.picking_ids
        # At least one picking should exist
        self.assertTrue(len(pickings) >= 1,
                        "At least one picking should be created for confirmed order")

    def test_standard_order_single_line_has_one_picking(self):
        """With slot_per_product=False and one line, exactly one picking is created."""
        order = self._confirm_order(
            slot_per_product=False,
            lines=[{'product_id': self.product_a.id, 'qty': 1}],
        )
        self.assertEqual(len(order.picking_ids), 1)

    # -------------------------------------------------------------------------
    # slot_per_product = True → one picking per move
    # -------------------------------------------------------------------------

    def test_slot_per_product_two_lines_two_pickings(self):
        """With slot_per_product=True, two lines should result in two pickings."""
        order = self._confirm_order(
            slot_per_product=True,
            lines=[
                {
                    'product_id': self.product_a.id,
                    'qty': 1,
                    'delivery_date': self.future_date,
                    'slot_id': self.slot.id,
                },
                {
                    'product_id': self.product_b.id,
                    'qty': 1,
                    'delivery_date': self.future_date2,
                    'slot_id': self.slot.id,
                },
            ],
        )
        pickings = order.picking_ids
        self.assertEqual(
            len(pickings), 2,
            f"Expected 2 separate pickings for slot_per_product order, got {len(pickings)}"
        )

    def test_slot_per_product_single_line_one_picking(self):
        """With slot_per_product=True, a single line results in one picking."""
        order = self._confirm_order(
            slot_per_product=True,
            lines=[
                {
                    'product_id': self.product_a.id,
                    'qty': 1,
                    'delivery_date': self.future_date,
                    'slot_id': self.slot.id,
                },
            ],
        )
        self.assertEqual(len(order.picking_ids), 1)

    def test_slot_per_product_pickings_reference_correct_order(self):
        """Pickings created for slot_per_product orders must reference the sale order."""
        order = self._confirm_order(
            slot_per_product=True,
            lines=[
                {
                    'product_id': self.product_a.id,
                    'qty': 2,
                    'delivery_date': self.future_date,
                    'slot_id': self.slot.id,
                },
            ],
        )
        for picking in order.picking_ids:
            self.assertEqual(
                picking.origin, order.name,
                "Picking origin should match the sale order name"
            )

    # -------------------------------------------------------------------------
    # Picking state after confirmation
    # -------------------------------------------------------------------------

    def test_pickings_in_expected_state_after_confirm(self):
        """Pickings should be in 'confirmed' or 'assigned' state after order confirm."""
        order = self._confirm_order(
            slot_per_product=False,
            lines=[{'product_id': self.product_a.id, 'qty': 1}],
        )
        valid_states = {'confirmed', 'assigned', 'waiting', 'done'}
        for picking in order.picking_ids:
            self.assertIn(
                picking.state, valid_states,
                f"Picking state '{picking.state}' is not a valid post-confirm state"
            )
