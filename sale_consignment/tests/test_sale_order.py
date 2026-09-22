# -*- coding: utf-8 -*-
from odoo.tests.common import tagged
from odoo import Command
from datetime import date, timedelta
from .common import TestConsignmentCommon


@tagged('post_install', '-at_install')
class TestSaleOrder(TestConsignmentCommon):

    def test_create_and_view_sale_order(self):
        """Test creating and viewing sale order from consignment."""
        consignment = self.env['sale.consignment'].create({
            'partner_id': self.partner_consignment.id,
            'end_date': date.today() + timedelta(days=10),
            'location_id': self.location_src.id,
            'consignment_line_ids': [
                Command.create({
                    'product_id': self.product_consignment.id,
                    'demand_quantity': 5,
                })
            ]
        })

        action = consignment.create_sale_order()
        self.assertTrue(consignment.sale_order_id)
        self.assertEqual(consignment.sale_count, 1)

        # Check action dict
        self.assertEqual(action['res_model'], 'sale.order')
        self.assertEqual(action['res_id'], consignment.sale_order_id.id)
        self.assertEqual(action['view_mode'], 'form')

        # Check sale order fields
        sale_order = consignment.sale_order_id
        self.assertEqual(sale_order.partner_id, self.partner_consignment)
        self.assertEqual(sale_order.consignment_id, consignment)
        self.assertEqual(sale_order.user_id, consignment.user_id)
        self.assertEqual(len(sale_order.order_line), 1)
        self.assertEqual(sale_order.order_line[0].product_id, self.product_consignment)
        self.assertEqual(sale_order.order_line[0].product_uom_qty, 1.0)

        # Test view order action
        view_action = consignment.action_view_order()
        self.assertEqual(view_action['res_model'], 'sale.order')
        self.assertEqual(view_action['domain'], [('consignment_id', 'in', [consignment.id])])
