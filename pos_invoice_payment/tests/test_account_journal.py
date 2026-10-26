# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
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
