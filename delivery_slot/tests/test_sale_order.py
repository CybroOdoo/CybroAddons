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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestSaleOrder(TransactionCase):
    """Test cases for the sale.order and sale.order.line extensions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleOrderLine = cls.env['sale.order.line']
        cls.DeliverySlot = cls.env['delivery.slot']
        cls.SlotTime = cls.env['slot.time']
        cls.IrConfig = cls.env['ir.config_parameter'].sudo()

        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
        })
        cls.slot_morning = cls.SlotTime.create({
            'name': 'Morning 8-12',
            'time_from': '8',
            'time_to': '12',
        })
        cls.slot_afternoon = cls.SlotTime.create({
            'name': 'Afternoon 13-17',
            'time_from': '13',
            'time_to': '17',
        })
        cls.future_date = date.today() + timedelta(days=5)
        cls.future_date2 = date.today() + timedelta(days=6)

    def _make_order(self, slot_per_product=True):
        """Helper: create a basic sale.order."""
        return self.SaleOrder.create({
            'partner_id': self.partner.id,
            'slot_per_product': slot_per_product,
        })

    def _make_line(self, order, delivery_date=None, slot_id=None, qty=1):
        """Helper: create a sale.order.line on the given order."""
        vals = {
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': qty,
        }
        if delivery_date:
            vals['delivery_date'] = delivery_date
        if slot_id:
            vals['slot_id'] = slot_id
        return self.SaleOrderLine.create(vals)

    # -------------------------------------------------------------------------
    # SaleOrder — new fields
    # -------------------------------------------------------------------------

    def test_slot_per_product_field_default_from_config(self):
        """Test slot_per_product defaults via ir.config_parameter."""
        self.IrConfig.set_param('delivery_slot.enable_delivery_date', False)
        order = self.SaleOrder.create({'partner_id': self.partner.id})
        self.assertFalse(order.slot_per_product)

    def test_slot_per_product_can_be_set_true(self):
        """Test slot_per_product can be explicitly set to True."""
        order = self._make_order(slot_per_product=True)
        self.assertTrue(order.slot_per_product)

    def test_delivery_slot_id_field_exists(self):
        """Test that delivery_slot_id Many2one field is accessible on sale.order."""
        order = self._make_order()
        self.assertFalse(order.delivery_slot_id)

    def test_slot_count_zero_on_draft(self):
        """Test slot_count is 0 when the order is in draft state."""
        order = self._make_order()
        self.assertEqual(order.slot_count, 0)

    # -------------------------------------------------------------------------
    # action_confirm — slot_per_product = False (standard flow)
    # -------------------------------------------------------------------------

    def test_confirm_order_without_slot_per_product(self):
        """Test confirming an order with slot_per_product=False works normally."""
        order = self._make_order(slot_per_product=False)
        self._make_line(order)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    # -------------------------------------------------------------------------
    # action_confirm — slot_per_product = True
    # -------------------------------------------------------------------------

    def test_confirm_creates_delivery_slot_when_missing(self):
        """Test confirming creates a new delivery.slot when none exists for date+slot."""
        order = self._make_order(slot_per_product=True)
        self._make_line(order, self.future_date, self.slot_morning.id)

        existing = self.DeliverySlot.search([
            ('delivery_date', '=', self.future_date),
            ('slot_id', '=', self.slot_morning.id),
        ])
        existing.unlink()  # ensure clean state

        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        new_slot = self.DeliverySlot.search([
            ('delivery_date', '=', self.future_date),
            ('slot_id', '=', self.slot_morning.id),
        ])
        self.assertTrue(new_slot, "A new delivery slot should have been created on confirm")

    def test_confirm_raises_when_slot_inactive(self):
        """Test that a ValidationError is raised when picking an inactive delivery slot.

        The _check_delivery_slot_limit @api.constrains fires at order line
        *creation* time (not at confirm), so the error surfaces in _make_line.
        """
        self.DeliverySlot.create({
            'delivery_date': self.future_date2,
            'slot_id': self.slot_afternoon.id,
            'active': False,
        })
        order = self._make_order(slot_per_product=True)
        with self.assertRaises(ValidationError):
            # The constraint fires here, before action_confirm is ever reached
            self._make_line(order, self.future_date2, self.slot_afternoon.id)

    def test_confirm_raises_when_slot_limit_reached(self):
        """Test that a ValidationError is raised when the delivery slot is full.

        The _check_delivery_slot_limit @api.constrains fires at order line
        *creation* time, so the error surfaces in _make_line.
        """
        self.DeliverySlot.create({
            'delivery_date': self.future_date,
            'slot_id': self.slot_afternoon.id,
            'delivery_limit': 0,
            'active': True,
        })
        order = self._make_order(slot_per_product=True)
        with self.assertRaises(ValidationError):
            # The constraint fires here, before action_confirm is ever reached
            self._make_line(order, self.future_date, self.slot_afternoon.id)

    # -------------------------------------------------------------------------
    # action_view_delivery_slot
    # -------------------------------------------------------------------------

    def test_action_view_delivery_slot_returns_action(self):
        """Test action_view_delivery_slot returns a valid act_window action."""
        order = self._make_order(slot_per_product=True)
        self._make_line(order, self.future_date, self.slot_morning.id)
        order.action_confirm()

        action = order.action_view_delivery_slot()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'delivery.slot')
        self.assertIn('list', action['view_mode'])
        self.assertIn('form', action['view_mode'])

    def test_action_view_delivery_slot_draft_order_returns_empty(self):
        """Test action_view_delivery_slot on a draft order returns empty domain."""
        order = self._make_order(slot_per_product=True)
        action = order.action_view_delivery_slot()
        self.assertEqual(action['domain'], [('id', 'in', [])])

    # -------------------------------------------------------------------------
    # _compute_delivery_slot_count
    # -------------------------------------------------------------------------

    def test_slot_count_after_confirm(self):
        """Test slot_count is > 0 after order confirmation."""
        order = self._make_order(slot_per_product=True)
        # Make sure no existing slot for this date
        self.DeliverySlot.search([
            ('delivery_date', '=', self.future_date),
            ('slot_id', '=', self.slot_morning.id),
        ]).unlink()
        self._make_line(order, self.future_date, self.slot_morning.id)
        order.action_confirm()
        self.assertGreater(order.slot_count, 0)

    def test_slot_count_zero_when_slot_per_product_false(self):
        """Test slot_count stays 0 when slot_per_product is False."""
        order = self._make_order(slot_per_product=False)
        self._make_line(order)
        order.action_confirm()
        self.assertEqual(order.slot_count, 0)


class TestSaleOrderLine(TransactionCase):
    """Test cases for sale.order.line extensions in delivery_slot."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SaleOrder = cls.env['sale.order']
        cls.SaleOrderLine = cls.env['sale.order.line']
        cls.DeliverySlot = cls.env['delivery.slot']
        cls.SlotTime = cls.env['slot.time']

        cls.partner = cls.env['res.partner'].create({'name': 'SOL Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'SOL Product',
            'type': 'consu',
        })
        cls.slot = cls.SlotTime.create({
            'name': 'Test Slot',
            'time_from': '9',
            'time_to': '11',
        })
        cls.future_date = date.today() + timedelta(days=7)
        cls.past_date = date.today() - timedelta(days=1)

    def _make_order(self):
        return self.SaleOrder.create({
            'partner_id': self.partner.id,
            'slot_per_product': True,
        })

    # -------------------------------------------------------------------------
    # New fields on sale.order.line
    # -------------------------------------------------------------------------

    def test_delivery_date_field_on_line(self):
        """Test delivery_date field is accessible on sale.order.line."""
        order = self._make_order()
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'delivery_date': self.future_date,
        })
        self.assertEqual(line.delivery_date, self.future_date)

    def test_slot_id_field_on_line(self):
        """Test slot_id Many2one field is accessible on sale.order.line."""
        order = self._make_order()
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'slot_id': self.slot.id,
        })
        self.assertEqual(line.slot_id.id, self.slot.id)

    def test_delivery_slot_id_field_on_line(self):
        """Test delivery_slot_id Many2one field is accessible on sale.order.line."""
        order = self._make_order()
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
        })
        self.assertFalse(line.delivery_slot_id)

    # -------------------------------------------------------------------------
    # _check_delivery_date constraint
    # -------------------------------------------------------------------------

    def test_past_delivery_date_raises_validation_error(self):
        """Test that a past delivery_date raises ValidationError."""
        order = self._make_order()
        with self.assertRaises(ValidationError):
            self.SaleOrderLine.create({
                'order_id': order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'delivery_date': self.past_date,
            })

    def test_today_delivery_date_is_valid(self):
        """Test that today's date is accepted.

        The _check_delivery_date constraint raises only when
        delivery_date < fields.Date.today() (strictly in the past).
        Today itself satisfies date >= today, so it must be allowed.
        """
        order = self._make_order()
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'delivery_date': date.today(),
        })
        self.assertEqual(line.delivery_date, date.today())

    def test_future_delivery_date_is_valid(self):
        """Test that a future delivery_date passes the constraint."""
        order = self._make_order()
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'delivery_date': self.future_date,
        })
        self.assertEqual(line.delivery_date, self.future_date)

    def test_no_delivery_date_no_error(self):
        """Test that a line without a delivery_date passes the constraint."""
        order = self._make_order()
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
        })
        self.assertFalse(line.delivery_date)

    # -------------------------------------------------------------------------
    # _check_delivery_slot_limit constraint
    # -------------------------------------------------------------------------

    def test_slot_limit_constraint_inactive_slot_raises(self):
        """Test ValidationError when picking an inactive delivery slot."""
        self.DeliverySlot.create({
            'delivery_date': self.future_date,
            'slot_id': self.slot.id,
            'active': False,
        })
        order = self._make_order()
        with self.assertRaises(ValidationError):
            self.SaleOrderLine.create({
                'order_id': order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'delivery_date': self.future_date,
                'slot_id': self.slot.id,
            })

    def test_slot_limit_constraint_full_slot_raises(self):
        """Test ValidationError when delivery slot has no remaining capacity."""
        future = date.today() + timedelta(days=8)
        slot2 = self.SlotTime.create({
            'name': 'Full Slot',
            'time_from': '14',
            'time_to': '16',
        })
        self.DeliverySlot.create({
            'delivery_date': future,
            'slot_id': slot2.id,
            'delivery_limit': 0,
            'active': True,
        })
        order = self._make_order()
        with self.assertRaises(ValidationError):
            self.SaleOrderLine.create({
                'order_id': order.id,
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'delivery_date': future,
                'slot_id': slot2.id,
            })

    def test_slot_limit_constraint_passes_when_capacity_available(self):
        """Test no error when delivery slot has remaining capacity."""
        future = date.today() + timedelta(days=9)
        slot3 = self.SlotTime.create({
            'name': 'Available Slot',
            'time_from': '15',
            'time_to': '17',
        })
        self.DeliverySlot.create({
            'delivery_date': future,
            'slot_id': slot3.id,
            'delivery_limit': 50,
            'active': True,
        })
        order = self._make_order()
        line = self.SaleOrderLine.create({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'delivery_date': future,
            'slot_id': slot3.id,
        })
        self.assertEqual(line.slot_id.id, slot3.id)

    # -------------------------------------------------------------------------
    # _onchange_slot_id_date
    # -------------------------------------------------------------------------

    def test_onchange_slot_id_date_no_date_empty_domain(self):
        """Test _onchange_slot_id_date returns empty domain when no date set."""
        order = self._make_order()
        line = self.SaleOrderLine.new({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
        })
        result = line._onchange_slot_id_date()
        self.assertIn('domain', result)
        self.assertEqual(result['domain']['slot_id'], [])

    def test_onchange_slot_id_date_with_future_date(self):
        """Test _onchange_slot_id_date with a valid future date returns a domain dict."""
        order = self._make_order()
        line = self.SaleOrderLine.new({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'delivery_date': self.future_date,
        })
        result = line._onchange_slot_id_date()
        self.assertIn('domain', result)
        self.assertIn('slot_id', result['domain'])

    def test_onchange_slot_id_clears_unavailable_slot(self):
        """Test that selecting an inactive slot triggers a warning and clears slot_id."""
        future = date.today() + timedelta(days=10)
        slot_inactive = self.SlotTime.create({
            'name': 'Inactive Time',
            'time_from': '20',
            'time_to': '22',
        })
        self.DeliverySlot.create({
            'delivery_date': future,
            'slot_id': slot_inactive.id,
            'active': False,
        })
        order = self._make_order()
        line = self.SaleOrderLine.new({
            'order_id': order.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'delivery_date': future,
            'slot_id': slot_inactive.id,
        })
        result = line._onchange_slot_id_date()
        self.assertIn('warning', result,
                      "Should return a warning for inactive slot")
        self.assertFalse(line.slot_id,
                         "slot_id should be cleared for unavailable slot")