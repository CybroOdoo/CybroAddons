# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'sale_quotation_revision')
class TestSaleOrderConfirmWizard(TransactionCase):
    """Tests for the SaleOrderConfirmWizard transient model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Wizard Test Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Wizard Test Product',
            'type': 'service',
            'list_price': 50.0,
        })

    def _make_order(self):
        return self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 50.0,
            })],
        })

    def _make_wizard(self, order, related_orders=None):
        related_ids = related_orders.ids if related_orders else []
        return self.env['sale.order.confirm.wizard'].create({
            'order_id': order.id,
            'sale_orders_ids': [(6, 0, related_ids)],
        })

    # ------------------------------------------------------------------
    # 1. Model / field presence
    # ------------------------------------------------------------------

    def test_field_order_id_exists(self):
        """order_id Many2one field must exist on the wizard."""
        self.assertIn('order_id', self.env['sale.order.confirm.wizard']._fields)

    def test_field_sale_orders_ids_exists(self):
        """sale_orders_ids Many2many field must exist on the wizard."""
        self.assertIn('sale_orders_ids', self.env['sale.order.confirm.wizard']._fields)

    def test_field_order_id_is_many2one(self):
        """check order_id is a  Many2many field ."""
        field = self.env['sale.order.confirm.wizard']._fields['order_id']
        self.assertEqual(field.type, 'many2one')
        self.assertEqual(field.comodel_name, 'sale.order')

    def test_field_sale_orders_ids_is_many2many(self):
        """check sale_orders_ids is a  Many2many field ."""
        field = self.env['sale.order.confirm.wizard']._fields['sale_orders_ids']
        self.assertEqual(field.type, 'many2many')
        self.assertEqual(field.comodel_name, 'sale.order')

    # ------------------------------------------------------------------
    # 2. action_rev_cancel_orders
    # ------------------------------------------------------------------

    def test_cancel_action_confirms_main_order(self):
        """action_rev_cancel_orders must confirm the main order_id."""
        order = self._make_order()
        wizard = self._make_wizard(order)
        wizard.action_rev_cancel_orders()
        self.assertEqual(order.state, 'sale')

    def test_cancel_action_sets_rev_confirm(self):
        """action_rev_cancel_orders must set rev_confirm=True on the main order."""
        order = self._make_order()
        wizard = self._make_wizard(order)
        wizard.action_rev_cancel_orders()
        self.assertTrue(order.rev_confirm)

    def test_cancel_action_cancels_related_orders(self):
        """action_rev_cancel_orders must cancel all orders in sale_orders_ids."""
        order = self._make_order()
        other = self._make_order()
        wizard = self._make_wizard(order, related_orders=other)
        wizard.action_rev_cancel_orders()
        self.assertEqual(other.state, 'cancel')

    def test_cancel_action_returns_close(self):
        """action_rev_cancel_orders must return act_window_close."""
        order = self._make_order()
        wizard = self._make_wizard(order)
        result = wizard.action_rev_cancel_orders()
        self.assertEqual(result.get('type'), 'ir.actions.act_window_close')

    def test_cancel_action_with_no_related_orders(self):
        """action_rev_cancel_orders must work when sale_orders_ids is empty."""
        order = self._make_order()
        wizard = self._make_wizard(order)
        result = wizard.action_rev_cancel_orders()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(result.get('type'), 'ir.actions.act_window_close')

    def test_cancel_action_multiple_related_orders(self):
        """action_rev_cancel_orders must cancel all related orders, not just one."""
        order = self._make_order()
        o2 = self._make_order()
        o3 = self._make_order()
        wizard = self._make_wizard(order, related_orders=o2 | o3)
        wizard.action_rev_cancel_orders()
        self.assertEqual(o2.state, 'cancel')
        self.assertEqual(o3.state, 'cancel')

    # ------------------------------------------------------------------
    # 3. action_rev_keep_orders
    # ------------------------------------------------------------------

    def test_keep_action_confirms_main_order(self):
        """action_rev_keep_orders must confirm the main order_id."""
        order = self._make_order()
        wizard = self._make_wizard(order)
        wizard.action_rev_keep_orders()
        self.assertEqual(order.state, 'sale')

    def test_keep_action_sets_rev_confirm(self):
        """action_rev_keep_orders must set rev_confirm=True on the main order."""
        order = self._make_order()
        wizard = self._make_wizard(order)
        wizard.action_rev_keep_orders()
        self.assertTrue(order.rev_confirm)

    def test_keep_action_does_not_cancel_related_orders(self):
        """action_rev_keep_orders must leave related orders in their current state."""
        order = self._make_order()
        other = self._make_order()
        wizard = self._make_wizard(order, related_orders=other)
        wizard.action_rev_keep_orders()
        self.assertNotEqual(other.state, 'cancel')

    def test_keep_action_returns_close(self):
        """action_rev_keep_orders must return act_window_close."""
        order = self._make_order()
        wizard = self._make_wizard(order)
        result = wizard.action_rev_keep_orders()
        self.assertEqual(result.get('type'), 'ir.actions.act_window_close')
