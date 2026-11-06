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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestChartTemplate(TransactionCase):
    """Wallet records are recreated after a chart of accounts is loaded"""

    def _wallet_records(self):
        journal = self.env.ref(
            'pos_customer_wallet_management.pos_wallet_journal_main',
            raise_if_not_found=False)
        payment_method = self.env.ref(
            'pos_customer_wallet_management.pos_wallet_payment_method_main',
            raise_if_not_found=False)
        return journal, payment_method

    def test_records_recreated_when_missing(self):
        journal, payment_method = self._wallet_records()
        payment_method.unlink()
        journal.unlink()
        self.assertEqual(self._wallet_records(), (None, None))
        chart = self.env['account.chart.template']
        chart._ensure_wallet_records(self.env.ref('base.main_company'))
        journal, payment_method = self._wallet_records()
        self.assertTrue(journal.is_wallet_journal)
        self.assertEqual(journal.code, 'WLT')
        self.assertEqual(payment_method.journal_id, journal)
        self.assertTrue(payment_method.is_wallet_journal)

    def test_existing_records_are_kept(self):
        journal, payment_method = self._wallet_records()
        self.env['account.chart.template']._ensure_wallet_records(
            self.env.ref('base.main_company'))
        self.assertEqual(self._wallet_records(), (journal, payment_method))

    def test_other_company_is_ignored(self):
        other = self.env['res.company'].create({'name': 'Other Company'})
        before = self.env['account.journal'].search_count(
            [('is_wallet_journal', '=', True)])
        self.env['account.chart.template']._ensure_wallet_records(other)
        after = self.env['account.journal'].search_count(
            [('is_wallet_journal', '=', True)])
        self.assertEqual(before, after)
