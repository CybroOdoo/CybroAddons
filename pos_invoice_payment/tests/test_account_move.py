# -*- coding: utf-8 -*-

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountMove(AccountTestInvoicingCommon):
    """Tests for account.move helpers added by pos_invoice_payment."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write({
            "group_ids": [Command.link(cls.env.ref("point_of_sale.group_pos_user").id)]
        })
        cls.invoice = cls.init_invoice(
            "out_invoice",
            partner=cls.partner_a,
            products=cls.product_a,
        )
        cls.vendor_bill = cls.init_invoice(
            "in_invoice",
            partner=cls.partner_b,
            products=cls.product_b,
        )

    def test_get_invoices_returns_customer_invoice_payloads(self):
        invoices = self.env["account.move"].get_invoices()
        invoice_by_id = {
            invoice_data["invoice_id"]: invoice_data for invoice_data in invoices
        }

        self.assertIn(self.invoice.id, invoice_by_id)
        self.assertNotIn(self.vendor_bill.id, invoice_by_id)
        self.assertEqual(
            invoice_by_id[self.invoice.id],
            {
                "invoice_id": self.invoice.id,
                "payment_reference": self.invoice.payment_reference,
                "partner_id": self.invoice.partner_id.name,
                "amount_total": self.invoice.amount_total,
                "amount_residual": self.invoice.amount_residual,
                "state": self.invoice.state,
                "payment_state": self.invoice.payment_state,
            },
        )

    def test_post_invoice_posts_draft_invoice(self):
        invoice = self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            products=self.product_a,
        )

        self.env["account.move"].post_invoice(invoice.id)

        self.assertEqual(invoice.state, "posted")

    def test_register_payment_posts_and_pays_invoice(self):
        invoice = self.init_invoice(
            "out_invoice",
            partner=self.partner_a,
            products=self.product_a,
        )

        self.env["account.move"].register_payment(invoice.id)

        self.assertEqual(invoice.state, "posted")
        self.assertIn(invoice.payment_state, ("in_payment", "paid"))
        self.assertEqual(invoice.amount_residual, 0.0)
