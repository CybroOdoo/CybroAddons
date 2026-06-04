# -*- coding: utf-8 -*-
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('post_install', '-at_install')
class TestPosActionLog(TestPoSCommon):

    def test_action_log_stores_restricted_action_details(self):
        product = self.env['product.product'].create({
            'name': 'Logged Restriction Product',
            'available_in_pos': True,
            'list_price': 9.0,
        })

        log = self.env['pos.action.log'].create({
            'user_id': self.env.user.id,
            'action_type': 'orderline_delete',
            'approved_by': self.env.user.id,
            'order_ref': 'ORDER-LOG-001',
            'product_id': product.id,
            'old_qty': 2.0,
            'new_qty': 0.0,
        })

        self.assertEqual(log.user_id, self.env.user)
        self.assertEqual(log.action_type, 'orderline_delete')
        self.assertEqual(log.approved_by, self.env.user)
        self.assertEqual(log.order_ref, 'ORDER-LOG-001')
        self.assertEqual(log.product_id, product)
        self.assertEqual(log.old_qty, 2.0)
        self.assertEqual(log.new_qty, 0.0)

    def test_action_log_has_expected_action_types(self):
        action_type_field = self.env['pos.action.log']._fields['action_type']

        self.assertEqual(
            dict(action_type_field.selection),
            {
                'orderline_quantity_update': 'Quantity Updated',
                'orderline_delete': 'Orderline Deleted',
                'delete_order': 'Order Deleted',
                'session_close': 'Session Close',
            },
        )
