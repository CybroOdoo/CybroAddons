# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import WalletCommon


@tagged('post_install', '-at_install')
class TestRechargeWallet(WalletCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_pos()

    def _wizard(self, amount):
        return self.env['recharge.wallet'].with_context(
            active_id=self.partner.id).create({
                'journal_id': self.wallet_journal.id,
                'recharge_amount': amount,
            })

    def test_default_journal_is_wallet_journal(self):
        wizard = self.env['recharge.wallet'].create({'recharge_amount': 1.0})
        self.assertEqual(wizard.journal_id, self.wallet_journal)

    def test_action_submit_rejects_zero_amount(self):
        with self.assertRaises(ValidationError):
            self._wizard(0.0).action_submit()

    def test_action_submit_rejects_negative_amount(self):
        with self.assertRaises(ValidationError):
            self._wizard(-5.0).action_submit()

    def test_action_submit_credits_wallet(self):
        payments_before = self.env['account.payment'].search_count(
            [('partner_id', '=', self.partner.id)])
        self._wizard(50.0).action_submit()

        self.assertEqual(self.partner.wallet_balance, 150.0)
        credit = self._transactions(self.partner, 'Credit')
        self.assertEqual(len(credit), 1)
        self.assertEqual(credit.amount, 50.0)
        payments_after = self.env['account.payment'].search_count(
            [('partner_id', '=', self.partner.id)])
        self.assertEqual(payments_after, payments_before + 1)
        payment = self.env['account.payment'].search(
            [('partner_id', '=', self.partner.id)], limit=1)
        self.assertEqual(payment.payment_type, 'inbound')
        self.assertEqual(payment.amount, 50.0)
        self.assertEqual(payment.journal_id, self.wallet_journal)

    def test_frontend_recharge_invalid_input(self):
        Wizard = self.env['recharge.wallet']
        self.assertFalse(Wizard.frontend_recharge(
            'abc', 10, 'USD', self.pos_session.id, self.wallet_journal.id))
        self.assertFalse(Wizard.frontend_recharge(
            self.partner.id, 'xyz', 'USD', self.pos_session.id,
            self.wallet_journal.id))
        self.assertFalse(Wizard.frontend_recharge(
            self.partner.id, 10, 'USD', self.pos_session.id, None))
        self.assertEqual(self.partner.wallet_balance, 100.0)

    def test_frontend_recharge_unknown_records(self):
        Wizard = self.env['recharge.wallet']
        self.assertFalse(Wizard.frontend_recharge(
            999999999, 10, 'USD', self.pos_session.id, self.wallet_journal.id))
        self.assertFalse(Wizard.frontend_recharge(
            self.partner.id, 10, 'USD', self.pos_session.id, 999999999))

    def test_frontend_recharge_success(self):
        result = self.env['recharge.wallet'].frontend_recharge(
            self.partner.id, '25.5', 'USD', self.pos_session.id,
            self.wallet_journal.id)
        self.assertAlmostEqual(result, 125.5)
        self.assertAlmostEqual(self.partner.wallet_balance, 125.5)
        credit = self._transactions(self.partner, 'Credit')
        self.assertEqual(len(credit), 1)
        self.assertAlmostEqual(credit.amount, 25.5)
        self.assertEqual(credit.currency, 'USD')
        self.assertEqual(credit.pos_order, self.pos_session.name)
        self.assertTrue(self.env['account.payment'].search_count([
            ('partner_id', '=', self.partner.id),
            ('payment_type', '=', 'inbound'),
        ]))

    def test_frontend_recharge_falls_back_when_session_is_invalid(self):
        self.env['recharge.wallet'].frontend_recharge(
            self.partner.id, 10, False, 'not-an-id', self.wallet_journal.id)
        credit = self._transactions(self.partner, 'Credit')
        self.assertEqual(len(credit), 1)
        self.assertTrue(credit.pos_order)
        # Currency falls back to the partner currency when none is passed.
        self.assertEqual(credit.currency, self.partner.currency_id.name)
