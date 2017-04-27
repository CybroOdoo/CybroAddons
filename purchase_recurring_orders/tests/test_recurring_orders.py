# -*- coding: utf-8 -*-
from openerp.tests import common


class TestRecurringOrder(common.TransactionCase):
    def setUp(self):
        super(TestRecurringOrder, self).setUp()
        self.agreement_model = self.env['purchase.recurring_orders.agreement']
        self.agreement = self.agreement_model.create(
            {'name': 'Agreement test',
             'partner_id': self.env.ref('base.res_partner_1').id})
        self.line_model = self.env['purchase.recurring_orders.agreement.line']
        self.agreement_line = self.line_model.create(
            {'agreement_id': self.agreement.id,
             'product_id': self.env.ref('product.product_product_1').id})
        self.agreement.generate_next_year_orders()

    def test_order_creation_next_year(self):
        self.assertEqual(len(self.agreement.order_line), 12)

    def test_order_creation_two_years(self):
        self.agreement.generate_next_orders(years=2)
        self.assertEqual(len(self.agreement.order_line), 24)

    def test_order_cleanup_change(self):
        self.agreement.active = False
        self.assertEqual(len(self.agreement.order_line), 0)

    def test_order_cleanup_change_with_confirmed_and_order_line(self):
        self.agreement.order_line[0].action_button_confirm()
        self.agreement.prolong_interval = 2
        self.assertEqual(len(self.agreement.order_line), 1)
