# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosDeleteOrderLine(TransactionCase):

    def setUp(self):
        super().setUp()

        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Config',
        })

        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'list_price': 100.0,
            'available_in_pos': True,
        })

        self.session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
            'user_id': self.env.uid,
        })

    def test_01_create_and_remove_orderline(self):
        """Test creating POS order and removing order line."""
        # Create order with minimal required values
        order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'user_id': self.env.uid,
            'pricelist_id': self.pos_config.pricelist_id.id,
            'amount_tax': 0.0,          # Required field
            'amount_total': 0.0,        # Required field
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })

        # Create order line
        line = self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'qty': 2,
            'price_unit': 100.0,
            'price_subtotal': 200.0,
            'price_subtotal_incl': 200.0,
        })

        self.assertEqual(len(order.lines), 1)
        self.assertEqual(line.qty, 2)

        # Test deletion of line (core functionality used by your module)
        line.unlink()
        self.assertEqual(len(order.lines), 0)

    def test_02_clear_all_orderlines(self):
        """Test removing all order lines at once."""
        order = self.env['pos.order'].create({
            'session_id': self.session.id,
            'user_id': self.env.uid,
            'pricelist_id': self.pos_config.pricelist_id.id,
            'amount_tax': 0.0,
            'amount_total': 0.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })

        # Create multiple lines
        self.env['pos.order.line'].create([
            {
                'order_id': order.id,
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 100.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            },
            {
                'order_id': order.id,
                'product_id': self.product.id,
                'qty': 3,
                'price_unit': 100.0,
                'price_subtotal': 300.0,
                'price_subtotal_incl': 300.0,
            }
        ])

        self.assertEqual(len(order.lines), 2)

        # Clear all lines
        order.lines.unlink()
        self.assertEqual(len(order.lines), 0)