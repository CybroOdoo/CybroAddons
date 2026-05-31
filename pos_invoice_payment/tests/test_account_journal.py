# -*- coding: utf-8 -*-
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestAccountJournal(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank_journal = cls.company_data['default_journal_bank']
        cls.cash_journal = cls.company_data['default_journal_cash']
        cls.general_journal = cls.company_data['default_journal_misc']

    def test_get_journal_returns_only_bank_and_cash_journals(self):
        journals = self.env['account.journal'].get_journal()
        returned_ids = {journal['id'] for journal in journals}

        self.assertIn(self.bank_journal.id, returned_ids)
        self.assertIn(self.cash_journal.id, returned_ids)
        self.assertNotIn(self.general_journal.id, returned_ids)
        self.assertIn(
            {'id': self.bank_journal.id, 'name': self.bank_journal.name},
            journals,
        )
