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
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountPartnerLedgerFilter(TransactionCase):
    """Tests for partner selection and initial balance report options."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Ledger Filter',
        })

    def test_get_wizard_uses_active_partners(self):
        """The partner action opens the ledger wizard with selected partners."""
        action = self.partner.with_context(active_ids=self.partner.ids).get_wizard()

        self.assertEqual(action['res_model'], 'account.report.partner.ledger')
        self.assertEqual(
            action['context']['default_partner_ids'], self.partner.ids,
        )

    def test_print_report_adds_partner_and_initial_balance_options(self):
        """The wizard forwards its partner filter and balance flag to the report."""
        wizard = self.env['account.report.partner.ledger'].create({
            'company_id': self.env.company.id,
            'partner_ids': [(6, 0, self.partner.ids)],
            'is_include_initial_balance': True,
        })

        report = self.env.ref('base_accounting_kit.action_report_partnerledger')
        with patch.object(type(report), 'report_action', return_value={}) as report_action:
            wizard._print_report({'form': {}})

        report_data = report_action.call_args.kwargs['data']
        self.assertEqual(report_data['form']['partner_ids'], self.partner.ids)
        self.assertTrue(report_data['form']['initial_balance'])
        self.assertIn('reconciled', report_data['form'])
        self.assertIn('amount_currency', report_data['form'])

    def test_print_report_without_initial_balance(self):
        """The initial balance option stays disabled when unchecked."""
        wizard = self.env['account.report.partner.ledger'].create({
            'company_id': self.env.company.id,
            'partner_ids': [(6, 0, self.partner.ids)],
            'is_include_initial_balance': False,
        })

        report = self.env.ref('base_accounting_kit.action_report_partnerledger')
        with patch.object(type(report), 'report_action', return_value={}) as report_action:
            wizard._print_report({'form': {}})

        report_data = report_action.call_args.kwargs['data']
        self.assertFalse(report_data['form']['initial_balance'])

    def test_report_requires_form_data(self):
        """Report generation fails clearly when its form payload is missing."""
        report = self.env['report.base_accounting_kit.report_partnerledger']

        with self.assertRaisesRegex(UserError, 'Form content is missing'):
            report._get_report_values([], data={})

    def test_get_report_values_without_initial_balance(self):
        """Report generation returns dictionary with docs when initial_balance is False."""
        report = self.env['report.base_accounting_kit.report_partnerledger']
        data = {
            'form': {
                'used_context': {},
                'target_move': 'posted',
                'result_selection': 'customer',
                'reconciled': True,
                'partner_ids': [self.partner.id],
                'initial_balance': False,
                'amount_currency': False,
                'date_from': False,
                'date_to': False,
                'journal_ids': [],
            },
        }
        res = report._get_report_values([], data=data)
        self.assertIn('docs', res)
        self.assertIn('doc_ids', res)
        self.assertEqual(res['doc_ids'], [self.partner.id])

    def test_get_report_values_with_initial_balance(self):
        """Report generation returns dictionary with response when initial_balance is True."""
        report = self.env['report.base_accounting_kit.report_partnerledger']
        data = {
            'form': {
                'used_context': {},
                'target_move': 'all',
                'result_selection': 'customer',
                'reconciled': False,
                'partner_ids': [self.partner.id],
                'initial_balance': True,
                'amount_currency': True,
                'date_from': '2026-01-01',
                'date_to': '2026-12-31',
                'journal_ids': [],
            },
        }
        res = report._get_report_values([], data=data)
        self.assertIn('docs', res)
        self.assertIn('response', res)
