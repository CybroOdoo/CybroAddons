from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('-at_install', 'post_install')
class TestPosPayment(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()

    def _create_order(self):
        return self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': self.session.id,
            'partner_id': self.customer.id,
            'pricelist_id': self.config.pricelist_id.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
            'state': 'paid',
            'last_order_preparation_change': '{}',
        })

    def test_create_payment_moves_skips_pay_later_payment_method(self):
        order = self._create_order()
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'amount': 100.0,
            'payment_method_id': self.pay_later_pm.id,
            'payment_date': order.date_order,
        })

        moves = payment._create_payment_moves()

        self.assertFalse(moves)
        self.assertFalse(payment.account_move_id)

    def test_create_payment_moves_skips_zero_amount_payment(self):
        order = self._create_order()
        payment = self.env['pos.payment'].create({
            'pos_order_id': order.id,
            'amount': 0.0,
            'payment_method_id': self.cash_pm1.id,
            'payment_date': order.date_order,
        })

        moves = payment._create_payment_moves()

        self.assertFalse(moves)
        self.assertFalse(payment.account_move_id)
