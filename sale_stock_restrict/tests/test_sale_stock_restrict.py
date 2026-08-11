# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestSaleStockRestrict(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleStockRestrict, cls).setUpClass()

        # Create a product with type 'consu' to match the condition in action_confirm
        cls.product = cls.env['product.product'].create({
            'name': 'Test Consu Product',
            'type': 'consu',
        })
        if hasattr(cls.product, 'is_storable'):
            cls.product.is_storable = True

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

        # Update stock for the product (on hand quantity = 10)
        # In Odoo, we typically use stock.quant to update on hand qty directly for tests
        stock_location = cls.env.ref('stock.stock_location_stock')
        cls.env['stock.quant']._update_available_quantity(cls.product, stock_location, 10.0)

    def test_01_onchange_product_id(self):
        """Test _onchange_product_id based on on_hand_quantity and forecast_quantity"""
        # Set config to check on hand quantity
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.check_stock', 'on_hand_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
            })],
        })
        line = order.order_line[0]

        # Trigger onchange
        line._onchange_product_id()

        self.assertEqual(line.qty_available, self.product.qty_available)
        self.assertEqual(line.forecast_quantity, 0.0)

        # Set config to check forecast quantity
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.check_stock', 'forecast_quantity')
        
        # Trigger onchange again
        line._onchange_product_id()

        self.assertEqual(line.forecast_quantity, self.product.virtual_available)
        self.assertEqual(line.qty_available, 0.0)

    def test_02_action_confirm_on_hand_success(self):
        """Test confirming order when on hand quantity is sufficient"""
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.check_stock', 'on_hand_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
            })],
        })
        line = order.order_line[0]
        # Set the fields manually as they are computed on onchange in UI, but in code we can just call it
        line._onchange_product_id()

        # Should not raise any exception
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_03_action_confirm_on_hand_fail(self):
        """Test confirming order when on hand quantity is insufficient"""
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.check_stock', 'on_hand_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 15,
            })],
        })
        line = order.order_line[0]
        line._onchange_product_id()

        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_04_action_confirm_forecast_success(self):
        """Test confirming order when forecast quantity is sufficient"""
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.check_stock', 'forecast_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 5,
            })],
        })
        line = order.order_line[0]
        line._onchange_product_id()

        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_05_action_confirm_forecast_fail(self):
        """Test confirming order when forecast quantity is insufficient"""
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.product_restriction', True)
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.check_stock', 'forecast_quantity')

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 15,
            })],
        })
        line = order.order_line[0]
        line._onchange_product_id()

        with self.assertRaises(ValidationError):
            order.action_confirm()

    def test_06_action_confirm_no_restriction(self):
        """Test confirming order when restriction is disabled"""
        self.env['ir.config_parameter'].sudo().set_param('sale_stock_restrict.product_restriction', False)

        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 15,
            })],
        })
        
        # Even with high quantity, it should confirm since restriction is disabled
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
