from odoo import Command, fields
from odoo.tests.common import TransactionCase


class TestResPartner(TransactionCase):
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
        cls.purchase_journal = cls.env["account.journal"].search([
            *journal_domain,
            ("type", "=", "purchase"),
        ], limit=1)
        cls.bank_journal = cls.env["account.journal"].search([
            *journal_domain,
            ("type", "=", "bank"),
        ], limit=1)
        cls.income_account = cls.env["account.account"].search([
            *account_domain,
            ("account_type", "=", "income"),
            ("deprecated", "=", False),
        ], limit=1)
        cls.expense_account = cls.env["account.account"].search([
            *account_domain,
            ("account_type", "=", "expense"),
            ("deprecated", "=", False),
        ], limit=1)
        cls.partner_a = cls.env["res.partner"].create({
            "name": "Partner A",
            "company_id": False,
        })
        cls.partner_b = cls.env["res.partner"].create({
            "name": "Partner B",
            "company_id": False,
        })
        cls.unpaid_invoice = cls._create_out_invoice(cls.partner_a, 100.0)
        cls.partial_invoice = cls._create_out_invoice(cls.partner_a, 60.0)
        cls.paid_invoice = cls._create_out_invoice(cls.partner_a, 40.0)
        cls.other_partner_invoice = cls._create_out_invoice(cls.partner_b, 75.0)
        cls.vendor_bill = cls._create_in_invoice(cls.partner_a, 55.0)
        cls._pay_invoice(cls.paid_invoice)

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

    @classmethod
    def _create_in_invoice(cls, partner, amount, post=True):
        invoice = cls.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": partner.id,
            "journal_id": cls.purchase_journal.id,
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": [Command.create({
                "name": "Vendor bill line",
                "quantity": 1.0,
                "price_unit": amount,
                "account_id": cls.expense_account.id,
            })],
        })
        if post:
            invoice.action_post()
        return invoice

    @classmethod
    def _pay_invoice(cls, invoice):
        cls.env["account.payment.register"].with_context(
            active_model="account.move",
            active_ids=invoice.ids,
        ).create({
            "journal_id": cls.bank_journal.id,
            "payment_method_line_id": cls.bank_journal.inbound_payment_method_line_ids[:1].id,
        })._create_payments()
        invoice.invalidate_recordset()

    def test_compute_due_amount_only_counts_unpaid_customer_invoices(self):
        self.partner_a.invalidate_recordset(["due_amount"])

        self.assertEqual(
            self.partner_a.due_amount,
            self.unpaid_invoice.amount_residual + self.partial_invoice.amount_residual,
        )

    def test_action_view_due_statements_returns_due_customer_invoice_lines(self):
        action = self.partner_a.action_view_due_statements()
        due_line_ids = set(self.env["account.move.line"].search(action["domain"]).ids)
        expected_line_ids = set(
            (self.unpaid_invoice.invoice_line_ids + self.partial_invoice.invoice_line_ids).ids
        )

        self.assertEqual(action["res_model"], "account.move.line")
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["name"], "Due Statements")
        self.assertEqual(action["view_mode"], "tree,form")
        self.assertEqual(
            action["views"][0][0],
            self.env.ref("multiple_payment_for_outstanding_dues.account_move_line_view_list").id,
        )
        self.assertEqual(action["views"][1][0], self.env.ref("account.view_move_line_form").id)
        self.assertEqual(action["context"]["create"], False)
        self.assertEqual(action["context"]["search_default_group_by_invoices"], True)
        self.assertEqual(due_line_ids, expected_line_ids)
        self.assertNotIn(self.paid_invoice.invoice_line_ids.id, due_line_ids)
        self.assertNotIn(self.vendor_bill.invoice_line_ids.id, due_line_ids)
        self.assertNotIn(self.other_partner_invoice.invoice_line_ids.id, due_line_ids)
