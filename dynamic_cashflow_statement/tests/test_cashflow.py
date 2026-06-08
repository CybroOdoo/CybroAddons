# -*- coding: utf-8 -*-
################################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCashFlow(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.cashflow = cls.env['cashflow']

        cls.receivable_account = cls.env['account.account'].search([
            ('account_type', '=', 'asset_receivable')
        ], limit=1)

        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income')
        ], limit=1)

        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'sale')
        ], limit=1)

        cls.partner = cls.env['res.partner'].create({
            'name': 'Demo Customer',
        })

        cls.move = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': cls.journal.id,
            'line_ids': [
                (0, 0, {
                    'name': 'Debit Line',
                    'account_id': cls.receivable_account.id,
                    'partner_id': cls.partner.id,
                    'debit': 100.0,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': 'Credit Line',
                    'account_id': cls.income_account.id,
                    'debit': 0.0,
                    'credit': 100.0,
                }),
            ]
        })

        cls.move.action_post()

    def test_get_report_values(self):
        """Test get_report_values method."""

        result = self.cashflow.get_report_values()

        self.assertIn('fetched_data', result)
        self.assertIn('account_res', result)
        self.assertIsInstance(result['fetched_data'], list)

    def test_get_lines(self):
        """Test _get_lines method."""

        result = self.cashflow._get_lines(
            self.receivable_account,
            {}
        )

        self.assertTrue(result)
        self.assertEqual(
            result['account'],
            self.receivable_account.name
        )

        self.assertIn('move_lines', result)
        self.assertIn('journal_lines', result)

    def test_get_lines_empty(self):
        """Test _get_lines for account without entries."""

        empty_account = self.env['account.account'].create({
            'name': 'Empty Account',
            'code': 'X9999',
            'account_type': 'asset_current',
        })

        result = self.cashflow._get_lines(
            empty_account,
            {}
        )
        self.assertFalse(result)
        