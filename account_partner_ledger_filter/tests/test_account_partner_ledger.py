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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from lxml import html

from odoo.tests import common, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestReportPartnerLedger(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Report Partner'
        })
        cls.report_model = cls.env['report.base_accounting_kit.report_partnerledger']

    def test_get_report_values_missing_form(self):
        """Test if UserError is raised when form content is missing in data."""
        with self.assertRaises(UserError):
            self.report_model._get_report_values(docids=[], data={})

    def test_get_report_values_with_data(self):
        """Test if _get_report_values returns correct structured values."""
        data = {
            'form': {
                'used_context': {},
                'target_move': 'posted',
                'result_selection': 'customer',
                'reconciled': False,
                'partner_ids': self.partner.ids,
                'initial_balance': False,
                'date_from': False,
                'date_to': False,
                'journal_ids': [],
            }
        }
        res = self.report_model._get_report_values(docids=[], data=data)

        self.assertEqual(res.get('doc_ids'), self.partner.ids)
        self.assertEqual([d.id for d in res.get('docs')], self.partner.ids)
        self.assertEqual(res.get('doc_model')._name, 'res.partner')
        self.assertIn('docs', res)

    def test_missing_data(self):
        """An omitted payload produces the same useful validation error."""
        with self.assertRaises(UserError):
            self.report_model._get_report_values([])

    def test_account_types_and_opening_balances(self):
        """Only matching ledger accounts contribute to opening balances."""
        accounts = self.env['account.account']
        receivable = accounts.create({
            'name': 'Ledger Test Receivable', 'code': 'PLTESTREC',
            'account_type': 'asset_receivable', 'reconcile': True,
        })
        payable = accounts.create({
            'name': 'Ledger Test Payable', 'code': 'PLTESTPAY',
            'account_type': 'liability_payable', 'reconcile': True,
        })
        expense = accounts.create({
            'name': 'Ledger Test Expense', 'code': 'PLTESTEXP',
            'account_type': 'expense',
        })
        journal = self.env['account.journal'].create({
            'name': 'Ledger Test', 'code': 'PLT', 'type': 'general',
        })
        move = self.env['account.move'].create({
            'journal_id': journal.id, 'date': '2026-01-01',
            'line_ids': [
                (0, 0, {'account_id': receivable.id,
                        'partner_id': self.partner.id, 'debit': 100,
                        'date_maturity': '2026-01-01'}),
                (0, 0, {'account_id': expense.id, 'credit': 100}),
            ],
        })
        move.action_post()
        period_move = move.copy({'date': '2026-02-10'})
        period_move.action_post()
        excluded_partner = self.env['res.partner'].create({'name': 'Excluded Partner'})
        excluded_move = move.copy({'date': '2026-02-11'})
        excluded_move.line_ids.write({'partner_id': excluded_partner.id})
        excluded_move.action_post()
        for selection, expected in [
            ('customer', receivable), ('supplier', payable),
            ('customer_supplier', receivable | payable),
        ]:
            data = {'form': {
                'used_context': {'date_from': '2026-02-01', 'date_to': '2026-02-28',
                                 'strict_range': True}, 'target_move': 'posted',
                'result_selection': selection, 'reconciled': False,
                'partner_ids': self.partner.ids, 'initial_balance': True,
                'date_from': '2026-02-01', 'date_to': '2026-02-28',
                'amount_currency': False,
                'journal_ids': journal.ids,
            }}
            result = self.report_model._get_report_values([], data)
            selected = accounts.browse(data['computed']['account_ids'])
            self.assertTrue(expected <= selected)
            self.assertNotIn(expense, selected)
            self.assertEqual([p.id for p in result['docs']], self.partner.ids)
            if selection == 'supplier':
                self.assertFalse(result['response'])
            else:
                self.assertEqual(result['response'][0]['initial_debit'], 100)
                self.assertEqual(result['response'][0]['initial_credit'], 0)

                self.assertEqual(result['lines'](data, self.partner)[0]['debit'], 100)
                self.assertEqual(result['sum_partner'](data, self.partner, 'debit'), 100)
                report_html, _ = self.env['ir.actions.report']._render_qweb_html(
                    'base_accounting_kit.action_report_partnerledger',
                    docids=self.partner.ids, data=data)
                document = html.fromstring(report_html)
                opening = document.xpath('//tr[contains(@class, "ledger-opening")]')
                closing = document.xpath('//tr[contains(@class, "ledger-closing")]')
                self.assertEqual(len(opening), 1)
                self.assertEqual(len(closing), 1)
                self.assertIn('100', opening[0].text_content())
                self.assertIn('200', closing[0].text_content())
                self.assertNotIn('Excluded Partner', document.text_content())
                data['form']['initial_balance'] = False
                period_html, _ = self.env['ir.actions.report']._render_qweb_html(
                    'base_accounting_kit.action_report_partnerledger',
                    docids=self.partner.ids, data=data)
                period_document = html.fromstring(period_html)
                self.assertFalse(period_document.xpath(
                    '//tr[contains(@class, "ledger-opening") or '
                    'contains(@class, "ledger-closing")]'))

    def test_unselected_partners(self):
        """Automatic partner discovery works with an empty ledger."""
        data = {'form': {
            'used_context': {}, 'target_move': 'all',
            'result_selection': 'customer', 'reconciled': True,
            'partner_ids': [], 'initial_balance': False,
        }}
        result = self.report_model._get_report_values([], data)
        self.assertIn('docs', result)
        self.assertEqual(data['computed']['move_state'], ['draft', 'posted'])
