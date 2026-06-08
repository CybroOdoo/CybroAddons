# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
###############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestSaleOrderLineToPurchaseOrderLine(TransactionCase):
    """Test converting selected sale order lines to purchase order lines."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test Vendor',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'sale_ok': True,
            'purchase_ok': True,
            'list_price': 100.0,
            'standard_price': 42.0,
        })
        cls.second_product = cls.env['product.product'].create({
            'name': 'Second Test Product',
            'type': 'consu',
            'sale_ok': True,
            'purchase_ok': True,
            'list_price': 200.0,
            'standard_price': 84.0,
        })

    def _create_sale_order(self):
        """Create a sale order with one selected and one unselected line."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'name': self.product.name,
                    'product_uom_qty': 3.0,
                    'product_uom': self.product.uom_id.id,
                    'price_unit': 100.0,
                    'is_check': True,
                }),
                (0, 0, {
                    'product_id': self.second_product.id,
                    'name': self.second_product.name,
                    'product_uom_qty': 5.0,
                    'product_uom': self.second_product.uom_id.id,
                    'price_unit': 200.0,
                    'is_check': False,
                }),
            ],
        })
        return sale_order

    def test_convert_selected_line_to_new_purchase_order(self):
        """Selected sale order lines create a new purchase order for vendor."""
        sale_order = self._create_sale_order()
        sale_order.vendor_id = self.vendor

        action = sale_order.action_convert_po()

        purchase_order = self.env['purchase.order'].search([
            ('partner_id', '=', self.vendor.id),
            ('order_line.product_id', '=', self.product.id),
        ], limit=1)

        self.assertTrue(purchase_order)
        self.assertEqual(len(purchase_order.order_line), 1)
        self.assertEqual(purchase_order.order_line.product_id, self.product)
        self.assertEqual(purchase_order.order_line.name, self.product.name)
        self.assertEqual(purchase_order.order_line.product_qty, 3.0)
        self.assertEqual(
            purchase_order.order_line.price_unit,
            self.product.standard_price
        )
        self.assertEqual(action['tag'], 'display_notification')
        self.assertIn(
            'New Purchase Order has been placed',
            action['params']['message']
        )

    def test_convert_selected_line_to_existing_purchase_order(self):
        """Selected sale order lines are added to selected draft PO."""
        sale_order = self._create_sale_order()
        purchase_order = self.env['purchase.order'].create({
            'partner_id': self.vendor.id,
        })
        sale_order.purchase_id = purchase_order

        action = sale_order.action_convert_po()

        self.assertEqual(len(purchase_order.order_line), 1)
        self.assertEqual(purchase_order.order_line.product_id, self.product)
        self.assertEqual(purchase_order.order_line.product_qty, 3.0)
        self.assertEqual(
            purchase_order.order_line.price_unit,
            self.product.standard_price
        )
        self.assertEqual(action['tag'], 'display_notification')
        self.assertIn(
            'Selected Order Lines added to existing Purchase Order',
            action['params']['message']
        )

    def test_convert_requires_selected_sale_order_line(self):
        """Conversion requires at least one checked sale order line."""
        sale_order = self._create_sale_order()
        sale_order.order_line.write({'is_check': False})
        sale_order.vendor_id = self.vendor

        with self.assertRaisesRegex(ValidationError, 'Select Order Line'):
            sale_order.action_convert_po()

    def test_convert_requires_vendor_or_purchase_order(self):
        """Conversion requires either a vendor or an existing purchase order."""
        sale_order = self._create_sale_order()

        with self.assertRaisesRegex(
            ValidationError,
            'Select Vendor or Purchase Order'
        ):
            sale_order.action_convert_po()
