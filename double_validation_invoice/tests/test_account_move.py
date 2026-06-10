# -*- coding: utf-8 -*-

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountMove(AccountTestInvoicingCommon):
    """Tests for invoice double-validation approval flow."""

    def setUp(self):
        super().setUp()
        self.config = self.env["ir.config_parameter"].sudo()

    def _set_double_validation_config(self, enabled=True, first=100.0, second=1000.0):
        self.config.set_param(
            "double_validation_invoice.double_validation",
            "True" if enabled else "",
        )
        self.config.set_param("double_validation_invoice.first_valid_limit", first)
        self.config.set_param("double_validation_invoice.second_valid_limit", second)

    def _create_customer_invoice(self, amount):
        return self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            amounts=[amount],
            taxes=[],
        )

    def test_action_post_posts_invoice_when_double_validation_is_disabled(self):
        self._set_double_validation_config(enabled=False, first=100.0, second=1000.0)
        invoice = self._create_customer_invoice(1500.0)

        invoice.action_post()

        self.assertEqual(invoice.state, "posted")

    def test_action_post_sends_invoice_to_first_approval_above_first_limit(self):
        self._set_double_validation_config(enabled=True, first=100.0, second=1000.0)
        invoice = self._create_customer_invoice(500.0)

        result = invoice.action_post()

        self.assertTrue(result)
        self.assertEqual(invoice.state, "first_approval")

    def test_action_post_posts_invoice_at_or_below_first_limit(self):
        self._set_double_validation_config(enabled=True, first=100.0, second=1000.0)
        invoice = self._create_customer_invoice(100.0)

        invoice.action_post()

        self.assertEqual(invoice.state, "posted")

    def test_action_first_approval_posts_invoice_at_or_below_second_limit(self):
        self._set_double_validation_config(enabled=True, first=100.0, second=1000.0)
        invoice = self._create_customer_invoice(500.0)
        invoice.action_post()

        invoice.action_first_approval()

        self.assertEqual(invoice.state, "posted")

    def test_action_first_approval_sends_invoice_to_second_approval_above_second_limit(self):
        self._set_double_validation_config(enabled=True, first=100.0, second=1000.0)
        invoice = self._create_customer_invoice(1500.0)
        invoice.action_post()

        invoice.action_first_approval()

        self.assertEqual(invoice.state, "second_approval")

    def test_action_second_approval_posts_invoice(self):
        self._set_double_validation_config(enabled=True, first=100.0, second=1000.0)
        invoice = self._create_customer_invoice(1500.0)
        invoice.action_post()
        invoice.action_first_approval()

        invoice.action_second_approval()

        self.assertEqual(invoice.state, "posted")
