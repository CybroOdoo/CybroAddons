# -*- coding: utf-8 -*-
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from .common import AccountKitCommon


@tagged('post_install', '-at_install')
class TestCreditLimit(AccountKitCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_param(
            'customer_credit_limit', True)
        cls.partner_a.write({'active_limit': True, 'blocking_stage': 500.0})

    def _post_customer_invoice(self, amount):
        inv = self.init_invoice('out_invoice', partner=self.partner_a,
                                amounts=[amount], taxes=[])
        inv.action_post()
        return inv

    def test_enable_credit_limit_from_config(self):
        """enable_credit_limit follows the 'customer_credit_limit' config param."""
        self.assertTrue(self.partner_a.enable_credit_limit)

    def test_invoice_blocked_when_over_blocking_stage(self):
        """Posting an invoice is blocked once the partner's due exceeds the
        blocking amount."""
        # First invoice builds up the due amount (nothing due yet -> allowed).
        self._post_customer_invoice(1000.0)
        self.env.invalidate_all()
        self.assertGreaterEqual(self.partner_a.due_amount, 500.0)
        # Next invoice must be blocked.
        with self.assertRaises(UserError):
            self._post_customer_invoice(200.0)

    def test_warning_before_blocking_constraint(self):
        """warning_stage must stay below blocking_stage."""
        with self.assertRaises(UserError):
            self.partner_a.write({'warning_stage': 800.0, 'blocking_stage': 500.0})

    def test_sale_order_confirm_multi_record(self):
        """_action_confirm must handle several orders at once (v19 is
        multi-record) without an 'Expected singleton' error."""
        so_vals = {
            'partner_id': self.partner_b.id,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        }
        orders = self.env['sale.order'].sudo().create(
            [dict(so_vals), dict(so_vals)])
        # partner_b has no active credit limit -> should confirm both cleanly.
        orders.action_confirm()
        self.assertEqual(set(orders.mapped('state')), {'sale'})
