from unittest.mock import patch

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('-at_install', 'post_install')
class TestAccountPaymentRegister(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()

    def _create_order(self, state='invoiced', is_partial_payment=True):
        return self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': self.session.id,
            'partner_id': self.customer.id,
            'pricelist_id': self.config.pricelist_id.id,
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 50.0,
            'amount_return': 0.0,
            'state': state,
            'is_partial_payment': is_partial_payment,
            'last_order_preparation_change': '{}',
        })

    def test_action_create_payments_clears_partial_flag_on_current_invoiced_order(self):
        order = self._create_order()
        wizard = self.env['account.payment.register']

        with patch(
            'odoo.addons.account.wizard.account_payment_register'
            '.AccountPaymentRegister.action_create_payments',
            return_value={'type': 'ir.actions.act_window_close'},
        ):
            result = wizard.action_create_payments()

        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertFalse(order.is_partial_payment)

    def test_action_create_payments_keeps_partial_flag_without_open_session_order(self):
        order = self._create_order(state='paid')
        wizard = self.env['account.payment.register']

        with patch(
            'odoo.addons.account.wizard.account_payment_register'
            '.AccountPaymentRegister.action_create_payments',
            return_value=True,
        ):
            result = wizard.action_create_payments()

        self.assertTrue(result)
        self.assertTrue(order.is_partial_payment)
