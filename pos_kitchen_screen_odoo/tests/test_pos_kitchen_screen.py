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
############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosKitchenScreen(TransactionCase):
    """Test cases for the POS Kitchen Screen module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_category = cls.env['pos.category'].create({
            'name': 'Kitchen Category',
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Kitchen POS Config',
            'module_pos_restaurant': True,
        })
        cls.kitchen_screen = cls.env['kitchen.screen'].create({
            'pos_config_id': cls.pos_config.id,
            'pos_categ_ids': [(6, 0, [cls.pos_category.id])],
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Burger',
            'type': 'consu',
            'list_price': 100,
            'available_in_pos': True,
            'pos_categ_ids': [(6, 0, [cls.pos_category.id])],
        })
        # A new session starts in the 'opening_control' state, which is
        # enough to create orders for these tests.
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.env.user.id,
        })
        cls.order_count = 0

    def _create_order(self):
        """Create a POS order with one kitchen line."""
        type(self).order_count += 1
        return self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'pos_reference': 'KITCHEN-TEST-%04d' % self.order_count,
            'amount_tax': 0.0,
            'amount_total': 200.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 2,
                'price_unit': 100,
                'price_subtotal': 200.0,
                'price_subtotal_incl': 200.0,
            })],
        })

    def test_kitchen_screen_creation(self):
        """The kitchen screen gets a sequence and the right POS."""
        self.assertNotEqual(self.kitchen_screen.sequence, 'New')
        self.assertEqual(self.kitchen_screen.pos_config_id, self.pos_config)

    def test_pos_shop_domain_excludes_used_config(self):
        """A POS that already has a kitchen screen is not offered again."""
        domain = self.env['kitchen.screen']._pos_shop_id()
        configs = self.env['pos.config'].search(domain)
        self.assertNotIn(self.pos_config, configs)

    def test_preparation_time(self):
        """Preparation time set on the variant is stored on the template."""
        product = self.env['product.product'].create({
            'name': 'Pizza',
            'type': 'consu',
        })
        product.prepair_time_minutes = 20.5
        self.assertAlmostEqual(
            product.product_tmpl_id.prepair_time_minutes, 20.5, places=2)

    def test_order_creation(self):
        """A kitchen order is flagged as cooking and gets its prep time."""
        order = self._create_order()
        self.assertEqual(order.config_id, self.pos_config)
        self.assertTrue(order.is_cooking)
        self.assertEqual(order.order_status, 'draft')
        self.assertEqual(order.order_ref, order.name)
        self.assertTrue(order.lines.is_cooking)

    def test_average_prepare_time(self):
        """The prepare time is the sum of product time multiplied by qty."""
        self.product.prepair_time_minutes = 5.0
        order = self._create_order()
        self.assertAlmostEqual(order.avg_prepare_time, 10.0, places=2)

    def test_get_product_details(self):
        """Order line details are returned for the given line ids."""
        order = self._create_order()
        details = order.lines.get_product_details(order.lines.ids)
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['product_id'], self.product.id)
        self.assertEqual(details[0]['qty'], 2)

    def test_order_line_progress_change(self):
        """The line status toggles between 'ready' and 'waiting'."""
        line = self._create_order().lines[0]
        self.assertEqual(line.order_status, 'draft')
        line.order_progress_change()
        self.assertEqual(line.order_status, 'ready')
        line.order_progress_change()
        self.assertEqual(line.order_status, 'waiting')

    def test_order_progress_draft(self):
        """Accepting an order moves it and its lines to 'waiting'."""
        order = self._create_order()
        order.order_progress_draft()
        self.assertEqual(order.order_status, 'waiting')
        self.assertEqual(order.lines.order_status, 'waiting')

    def test_order_progress_change(self):
        """Completing an order moves it to 'ready'."""
        order = self._create_order()
        order.order_progress_change()
        self.assertEqual(order.order_status, 'ready')

    def test_order_progress_cancel(self):
        """Cancelling an order cancels its lines too."""
        order = self._create_order()
        order.order_progress_cancel()
        self.assertEqual(order.order_status, 'cancel')
        self.assertEqual(order.lines.order_status, 'cancel')

    def test_get_kitchen_orders(self):
        """Open kitchen orders are listed for the kitchen screen."""
        order = self._create_order()
        orders = self.env['pos.order'].get_kitchen_orders(self.pos_config.id)
        self.assertIn(order.id, [data['id'] for data in orders])

    def test_update_kitchen_order_status(self):
        """The kitchen order status can be updated by id."""
        order = self._create_order()
        result = self.env['pos.order'].update_kitchen_order_status(
            order.id, 'waiting')
        self.assertTrue(result)
        self.assertEqual(order.order_status, 'waiting')

    def test_check_order_status(self):
        """Items can be added while the order is cooking or waiting."""
        order = self._create_order()
        self.assertTrue(self.env['pos.order'].check_order_status(
            False, order.pos_reference))
        order.order_progress_change()
        self.assertFalse(self.env['pos.order'].check_order_status(
            False, order.pos_reference))

    def test_check_order(self):
        """An open kitchen order passes, a completed one does not."""
        order = self._create_order()
        self.assertTrue(
            self.env['pos.order'].check_order(order.pos_reference))
        order.order_progress_change()
        self.assertFalse(
            self.env['pos.order'].check_order(order.pos_reference))

    def test_check_order_unhandled_category(self):
        """Products of a category outside the kitchen are reported."""
        other_category = self.env['pos.category'].create({'name': 'Drinks'})
        other_product = self.env['product.product'].create({
            'name': 'Cola',
            'type': 'consu',
            'available_in_pos': True,
            'pos_categ_ids': [(6, 0, [other_category.id])],
        })
        order = self._create_order()
        self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': other_product.id,
            'qty': 1,
            'price_unit': 10,
            'price_subtotal': 10.0,
            'price_subtotal_incl': 10.0,
        })
        result = self.env['pos.order'].check_order(order.pos_reference)
        self.assertEqual(result, {'category': 'Drinks'})

    def test_get_details(self):
        """The kitchen screen receives the cooking orders and lines."""
        order = self._create_order()
        values = self.env['pos.order'].get_details(self.pos_config.id)
        self.assertIn(order.id, [rec['id'] for rec in values['orders']])
        self.assertEqual(
            [line['id'] for line in values['order_lines']], order.lines.ids)

    def test_process_order_for_kitchen(self):
        """An order created from the POS is sent to the kitchen."""
        order = self._create_order()
        order.name = 'Order %s' % order.pos_reference
        order.write({'is_cooking': False})
        result = self.env['pos.order'].process_order_for_kitchen({
            'pos_reference': order.pos_reference,
            'config_id': self.pos_config.id,
        })
        self.assertTrue(result)
        self.assertTrue(order.is_cooking)
        self.assertEqual(order.order_status, 'draft')
