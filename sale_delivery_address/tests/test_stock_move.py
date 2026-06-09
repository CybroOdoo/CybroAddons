# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestStockMove(TransactionCase):
    """Test cases for the StockMove model (stock.move extension)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a partner to use as customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Main Customer',
        })

        # Create sub-contacts of partner to use as delivery addresses
        cls.delivery_addr_1 = cls.env['res.partner'].create({
            'name': 'Delivery Address 1',
            'parent_id': cls.partner.id,
            'type': 'delivery',
        })
        cls.delivery_addr_2 = cls.env['res.partner'].create({
            'name': 'Delivery Address 2',
            'parent_id': cls.partner.id,
            'type': 'delivery',
        })

        # Create consumable products (generate stock moves/pickings upon SO confirmation)
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Storable Product 1',
            'type': 'consu',
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Storable Product 2',
            'type': 'consu',
        })

        # Create a Sale Order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_multiple_delivery_addresses_creates_separate_pickings(self):
        """Test that confirming an SO with different line addresses creates separate pickings."""
        # Create order lines with different delivery addresses
        self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_1.id,
            'product_uom_qty': 2.0,
            'delivery_addr_id': self.delivery_addr_1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': self.sale_order.id,
            'product_id': self.product_2.id,
            'product_uom_qty': 3.0,
            'delivery_addr_id': self.delivery_addr_2.id,
        })

        # Confirm the sales order
        self.sale_order.action_confirm()

        # Check that two separate pickings are created
        pickings = self.sale_order.picking_ids
        self.assertEqual(len(pickings), 2, "There should be exactly 2 pickings.")

        # Verify that each picking contains the correct partner address
        picking_partners = pickings.mapped('partner_id')
        self.assertIn(self.delivery_addr_1, picking_partners)
        self.assertIn(self.delivery_addr_2, picking_partners)

    def test_single_delivery_address_creates_single_picking(self):
        """Test that confirming an SO with the same line address creates a single picking."""
        # Create another sale order
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })

        # Create order lines using the same delivery address
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_1.id,
            'product_uom_qty': 1.0,
            'delivery_addr_id': self.delivery_addr_1.id,
        })
        self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_2.id,
            'product_uom_qty': 2.0,
            'delivery_addr_id': self.delivery_addr_1.id,
        })

        # Confirm the sales order
        sale_order.action_confirm()

        # Check that only one picking is created
        pickings = sale_order.picking_ids
        self.assertEqual(len(pickings), 1, "There should be exactly 1 picking when all lines use the same address.")
        self.assertEqual(pickings.partner_id, self.delivery_addr_1)
