from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestAccountMoveLine(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        account_domain = cls.env["account.account"]._check_company_domain(cls.company)
        journal_domain = cls.env["account.journal"]._check_company_domain(cls.company)
        cls.sale_journal = cls.env["account.journal"].search([
            *journal_domain,
            ("type", "=", "sale"),
        ], limit=1)
        cls.income_account = cls.env["account.account"].search([
            *account_domain,
            ("account_type", "=", "income"),
            ("deprecated", "=", False),
        ], limit=1)
        cls.partner_a = cls.env["res.partner"].create({
            "name": "Partner A",
            "company_id": False,
        })

    @classmethod
    def _create_out_invoice(cls, partner, amount, post=True):
        invoice = cls.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "journal_id": cls.sale_journal.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [Command.create({
                "name": "Invoice line",
                "quantity": 1.0,
                "price_unit": amount,
                "account_id": cls.income_account.id,
            })],
        })
        if post:
            invoice.action_post()
        return invoice

    def test_action_register_payment_uses_parent_move_ids(self):
        invoice_1 = self._create_out_invoice(self.partner_a, 150.0)
        invoice_2 = self._create_out_invoice(self.partner_a, 90.0)
        lines = invoice_1.invoice_line_ids + invoice_2.invoice_line_ids

        action = lines.action_register_payment()

        self.assertEqual(action["name"], "Register Payment")
        self.assertEqual(action["res_model"], "account.payment.register")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["context"]["active_model"], "account.move")
        self.assertEqual(action["context"]["active_ids"], (invoice_1 + invoice_2).ids)
