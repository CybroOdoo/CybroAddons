# -*- coding: utf-8 -*-

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccountJournal(AccountTestInvoicingCommon):
    """Tests for account.journal helpers added by pos_invoice_payment."""

    def test_get_journal_returns_bank_and_cash_journals(self):
        journals = self.env["account.journal"].get_journal()
        journal_ids = {journal["id"] for journal in journals}

        self.assertIn(self.company_data["default_journal_bank"].id, journal_ids)
        self.assertIn(self.company_data["default_journal_cash"].id, journal_ids)
        self.assertNotIn(self.company_data["default_journal_sale"].id, journal_ids)
        self.assertNotIn(self.company_data["default_journal_purchase"].id, journal_ids)
        self.assertTrue(
            all({"id", "name"} == set(journal) for journal in journals),
            "Journal payload must expose only id and name for POS usage.",
        )
