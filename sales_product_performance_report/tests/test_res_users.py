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

class TestResUsers(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use standard active company
        cls.company = cls.env.company

        # Create warehouse
        cls.warehouse = cls.env['stock.warehouse'].create({
            'name': 'Test Warehouse',
            'code': 'TWH',
            'company_id': cls.company.id,
        })

        # Create a sales team
        cls.sales_team = cls.env['crm.team'].create({
            'name': 'Test Sales Team',
            'company_id': cls.company.id,
        })
        
        # Create user / sales person
        cls.sales_person = cls.env['res.users'].create({
            'name': 'Test Sales Person',
            'login': 'test_sales_person',
            'email': 'test@example.com',
            'company_id': cls.company.id,
            'company_ids': [(6, 0, [cls.company.id])],
        })

        # Create crm.team.member to compute sale_team_id
        cls.env['crm.team.member'].create({
            'crm_team_id': cls.sales_team.id,
            'user_id': cls.sales_person.id,
        })
        
        # Create another sales team
        cls.other_sales_team = cls.env['crm.team'].create({
            'name': 'Other Sales Team',
            'company_id': cls.company.id,
        })

        # Create partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })

        # Create product template
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Product',
            'list_price': 10.0,
        })
        cls.product = cls.product_template.product_variant_id

        # Create sale orders
        cls.sale_order_1 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.sales_person.id,
            'team_id': cls.sales_team.id,
            'date_order': '2026-06-01 10:00:00',
            'company_id': cls.company.id,
        })
        # Create line to compute amount_total to 100
        cls.sale_order_line_1 = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order_1.id,
            'product_id': cls.product.id,
            'product_uom_qty': 10.0,
            'price_unit': 10.0,
            'tax_ids': [(5, 0, 0)],
        })
        cls.sale_order_1.state = 'draft' # Explicitly keep draft
        
        cls.sale_order_2 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.sales_person.id,
            'team_id': cls.sales_team.id,
            'date_order': '2026-06-02 10:00:00',
            'company_id': cls.company.id,
        })
        # Create line to compute amount_total to 200
        cls.sale_order_line_2 = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order_2.id,
            'product_id': cls.product.id,
            'product_uom_qty': 20.0,
            'price_unit': 10.0,
            'tax_ids': [(5, 0, 0)],
        })
        cls.sale_order_2.state = 'sale' # Mark as done / sale
        
        cls.sale_order_other = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.sales_person.id,
            'team_id': cls.other_sales_team.id,
            'date_order': '2026-06-03 10:00:00',
            'company_id': cls.company.id,
        })
        # Create line to compute amount_total to 300
        cls.sale_order_line_other = cls.env['sale.order.line'].create({
            'order_id': cls.sale_order_other.id,
            'product_id': cls.product.id,
            'product_uom_qty': 30.0,
            'price_unit': 10.0,
            'tax_ids': [(5, 0, 0)],
        })
        cls.sale_order_other.state = 'sale'

        # Create incoming stock picking for return
        incoming_picking_type = cls.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1)
        if not incoming_picking_type:
            incoming_picking_type = cls.env['stock.picking.type'].create({
                'name': 'Incoming',
                'code': 'incoming',
                'sequence_code': 'IN',
                'warehouse_id': cls.warehouse.id,
            })
        cls.picking_return = cls.env['stock.picking'].create({
            'picking_type_id': incoming_picking_type.id,
            'sale_id': cls.sale_order_2.id,
            'location_id': cls.env.ref('stock.stock_location_customers').id,
            'location_dest_id': cls.warehouse.lot_stock_id.id,
        })

    def setUp(self):
        super().setUp()
        self.mock_request = MagicMock()
        self.mock_request.env = self.env
        _request_stack.push(self.mock_request)

    def tearDown(self):
        _request_stack.pop()
        super().tearDown()

    def test_performance_values(self):
        # Call performance_values on the sales person record
        self.sales_person.performance_values(
            self.sales_person,
            Date.to_date('2026-05-01'),
            Date.to_date('2026-06-15'),
            False
        )
        self.assertEqual(self.sales_person.total_sale_order, 2)  # order 1 and 2
        self.assertEqual(self.sales_person.sale_order_done, 1)   # order 2 is done
        self.assertEqual(self.sales_person.net_revenue, 200.0)
        self.assertEqual(self.sales_person.estimated_revenue, 300.0)
        self.assertEqual(self.sales_person.avg_price, 150.0)
        self.assertEqual(self.sales_person.returned_orders, 1)   # 1 return picking

    def test_action_sale_order(self):
        # Test when there are orders in context date range
        try:
            action = self.sales_person.with_context(
                up_to_date=False,
                start_date='2026-05-01',
                end_date='2026-06-15'
            ).action_sale_order()
        except Exception as e:
            import logging
            logging.getLogger('test_res_users').exception("EXCEPTION IN ACTION_SALE_ORDER")
            raise
        self.assertEqual(action.get('res_model'), 'sale.order')
        self.assertIn(self.sale_order_1.id, action.get('domain')[0][2])
        self.assertIn(self.sale_order_2.id, action.get('domain')[0][2])

        # Test when there are no orders
        with self.assertRaises(UserError):
            self.sales_person.with_context(
                up_to_date=False,
                start_date='2026-06-10',
                end_date='2026-06-15'
            ).action_sale_order()


