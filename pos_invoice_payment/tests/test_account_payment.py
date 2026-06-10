# -*- coding: utf-8 -*-

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountPayment(AccountTestInvoicingCommon):
    """Tests for account.payment helpers added by pos_invoice_payment."""

    def test_create_payment_creates_posted_inbound_customer_payment(self):
        existing_payments = self.env["account.payment"].search([])

        self.env["account.payment"].create_payment(
            {
                "journal_id": str(self.company_data["default_journal_bank"].id),
                "partner_id": str(self.partner_a.id),
                "currency_id": str(self.company_data["currency"].id),
                "amount": "125.50",
            }
        )

        payment = self.env["account.payment"].search([]) - existing_payments
        self.assertEqual(len(payment), 1)
        self.assertRecordValues(
            payment,
            [
                {
                    "journal_id": self.company_data["default_journal_bank"].id,
                    "partner_id": self.partner_a.id,
                    "currency_id": self.company_data["currency"].id,
                    "amount": 125.50,
                    "payment_type": "inbound",
                    "partner_type": "customer",
                }
            ],
        )
        self.assertIn(payment.state, ("in_process", "paid"))
