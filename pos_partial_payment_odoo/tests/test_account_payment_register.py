# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged('-at_install', 'post_install')
class TestAccountPaymentRegister(TestPoSCommon):

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()
        self.payment_method = self.config.payment_method_ids[:1] or self.env['pos.payment.method'].create({
            'name': 'Test Cash',
            'receivable_account_id': self.env.company.account_default_pos_receivable_account_id.id or self.customer.property_account_receivable_id.id,
        })

    def _create_order(self, state='invoiced', is_partial_payment=True, amount_total=100.0, amount_paid=50.0):
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Item',
                'quantity': 1,
                'price_unit': amount_total,
            })],
        })
        try:
            invoice.action_post()
        except Exception:
            pass

        return self.env['pos.order'].create({
            'company_id': self.env.company.id,
            'session_id': self.session.id,
            'partner_id': self.customer.id,
            'pricelist_id': self.config.pricelist_id.id,
            'amount_tax': 0.0,
            'amount_total': amount_total,
            'amount_paid': amount_paid,
            'amount_return': 0.0,
            'state': state,
            'is_partial_payment': is_partial_payment,
            'account_move': invoice.id,
            'last_order_preparation_change': '{}',
        })

    def test_action_create_payments_clears_partial_flag_on_current_invoiced_order(self):
        order = self._create_order(state='invoiced', is_partial_payment=True, amount_total=100.0, amount_paid=50.0)
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=order.account_move.ids,
        ).create({
            'amount': 50.0,
            'pos_payment_method_id': self.payment_method.id,
        })

        with patch(
            'odoo.addons.account.wizard.account_payment_register'
            '.AccountPaymentRegister.action_create_payments',
            return_value={'type': 'ir.actions.act_window_close'},
        ):
            result = wizard.action_create_payments()

        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(order.amount_paid, 100.0)
        self.assertEqual(order.state, 'paid')
        self.assertFalse(order.is_partial_payment)

    def test_action_create_payments_keeps_partial_flag_when_not_fully_paid(self):
        order = self._create_order(state='invoiced', is_partial_payment=True, amount_total=100.0, amount_paid=30.0)
        wizard = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=order.account_move.ids,
        ).create({
            'amount': 20.0,
            'pos_payment_method_id': self.payment_method.id,
        })

        with patch(
            'odoo.addons.account.wizard.account_payment_register'
            '.AccountPaymentRegister.action_create_payments',
            return_value={'type': 'ir.actions.act_window_close'},
        ):
            result = wizard.action_create_payments()

        self.assertEqual(result, {'type': 'ir.actions.act_window_close'})
        self.assertEqual(order.amount_paid, 50.0)
        self.assertEqual(order.state, 'invoiced')
        self.assertTrue(order.is_partial_payment)
