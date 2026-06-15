# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from unittest.mock import MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.http import _request_stack

class TestProductTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use standard active company
        cls.company = cls.env.company
        
        # Create a partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        
        # Create product template
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Product Template',
            'list_price': 100.0,
            'type': 'consu',
            'is_storable': True,
        })
        cls.product_product = cls.product_template.product_variant_id

        # Create warehouse
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TWH',
            'company_id': cls.company.id,
        })

        # Create a stock quant to ensure stock_quant search returns something
        cls.quant = cls.env['stock.quant'].create({
            'product_id': cls.product_product.id,
            'location_id': cls.warehouse.lot_stock_id.id,
            'quantity': 50.0,
        })

        # Create a sale order
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'warehouse_id': cls.warehouse.id,
            'date_order': '2026-06-01 10:00:00',
        })
        
        # Create sale order line
        cls.sale_order_line = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order.id,
            'product_id': cls.product_product.id,
            'product_uom_qty': 5.0,
            'qty_delivered_method': 'manual',
            'qty_delivered': 5.0,
            'price_unit': 100.0,
        })
        
        # Confirm the sale order
        cls.sale_order.action_confirm()

        # Validate delivery picking to compute qty_delivered correctly
        for pick in cls.sale_order.picking_ids:
            for move in pick.move_ids:
                move.quantity = move.product_uom_qty
                move.picked = True
            pick.button_validate()

        # Reset date_order to the original past date
        cls.sale_order.write({'date_order': '2026-06-01 10:00:00'})

        # Find or create incoming picking type
        incoming_picking_type = cls.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        if not incoming_picking_type:
            incoming_picking_type = cls.env['stock.picking.type'].create({
                'name': 'Incoming',
                'code': 'incoming',
                'sequence_code': 'IN',
                'warehouse_id': cls.warehouse.id,
            })
        
        # Create picking for return
        picking = cls.env['stock.picking'].create({
            'picking_type_id': incoming_picking_type.id,
            'location_id': cls.env.ref('stock.stock_location_customers').id,
            'location_dest_id': cls.warehouse.lot_stock_id.id,
            'sale_id': cls.sale_order.id,
        })

        # Create stock move representing the return
        cls.stock_move = cls.env['stock.move'].create({
            'product_id': cls.product_product.id,
            'product_uom': cls.product_product.uom_id.id,
            'location_id': cls.env.ref('stock.stock_location_customers').id,
            'location_dest_id': cls.warehouse.lot_stock_id.id,
            'sale_line_id': cls.sale_order_line.id,
            'picking_id': picking.id,
            'picking_type_id': incoming_picking_type.id,
            'quantity': 2.0,
        })

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        _request_stack.push(self.mock_request)

    def tearDown(self):
        _request_stack.pop()
        super().tearDown()

    def test_performance_values_up_to_date(self):
        # Call performance_values with up_to_date=True
        self.product_template.performance_values(False, False, True)
        self.assertEqual(self.product_template.quantity, 45.0)
        self.assertEqual(self.product_template.stock_warehouse_id, self.warehouse)
        self.assertEqual(self.product_template.ordered_quantities, 5)
        self.assertEqual(self.product_template.delivered_quantities, 5)
        self.assertEqual(self.product_template.total_order, 1)
        self.assertEqual(self.product_template.avg_stock, 5.0)
        self.assertEqual(self.product_template.avg_qty_order, 5.0)
        self.assertEqual(self.product_template.avg_price, 100.0)
        self.assertEqual(self.product_template.revenue, 500.0)
        self.assertEqual(self.product_template.returned_quantities, 2)

    def test_performance_values_with_dates(self):
        # Call performance_values with date range including the sale order date
        self.product_template.performance_values(Date.to_date('2026-05-01'), Date.to_date('2026-06-15'), False)
        self.assertEqual(self.product_template.total_order, 1)

        # Call performance_values with date range excluding the sale order date
        self.product_template.performance_values(Date.to_date('2026-06-10'), Date.to_date('2026-06-15'), False)
        self.assertEqual(self.product_template.total_order, 0)

    def test_action_sale_order(self):
        # Test when there are orders
        action = self.product_template.with_context(
            up_to_date=False,
            start_date='2026-05-01',
            end_date='2026-06-15'
        ).action_sale_order()
        self.assertEqual(action.get('res_model'), 'sale.order')
        self.assertIn(self.sale_order.id, action.get('domain')[0][2])

        # Test when there are no orders in the date range
        with self.assertRaises(UserError):
            self.product_template.with_context(
                up_to_date=False,
                start_date='2026-06-10',
                end_date='2026-06-15'
            ).action_sale_order()

