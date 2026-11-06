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

from unittest.mock import patch

from odoo.tests import tagged

from .common import WalletCommon


@tagged('post_install', '-at_install')
class TestPosOrderWallet(WalletCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_pos()

    def test_deduct_wallet_amount(self):
        order = self._create_order(self.partner, [(self.wallet_pm, 40.0, False)])
        order._deduct_wallet_amount()

        self.assertEqual(self.partner.wallet_balance, 60.0)
        self.assertTrue(order.is_wallet_deducted)
        debit = self._transactions(self.partner, 'Debit')
        self.assertEqual(len(debit), 1)
        self.assertEqual(debit.amount, 40.0)
        self.assertEqual(debit.pos_order, order.pos_reference or order.name)

    def test_deduct_is_idempotent(self):
        order = self._create_order(self.partner, [(self.wallet_pm, 40.0, False)])
        order._deduct_wallet_amount()
        order._deduct_wallet_amount()
        self.assertEqual(self.partner.wallet_balance, 60.0)
        self.assertEqual(len(self._transactions(self.partner, 'Debit')), 1)

    def test_skip_when_already_flagged(self):
        order = self._create_order(self.partner, [(self.wallet_pm, 40.0, False)])
        order.is_wallet_deducted = True
        order._deduct_wallet_amount()
        self.assertEqual(self.partner.wallet_balance, 100.0)
        self.assertFalse(self._transactions(self.partner, 'Debit'))

    def test_skip_when_order_has_no_partner(self):
        order = self._create_order(
            self.partner, [(self.wallet_pm, 40.0, False)], partner_less=True)
        order._deduct_wallet_amount()
        self.assertFalse(order.is_wallet_deducted)
        self.assertFalse(self._transactions(self.partner, 'Debit'))
        self.assertEqual(self.partner.wallet_balance, 100.0)

    def test_skip_when_no_wallet_payment(self):
        order = self._create_order(self.partner, [(self.other_pm, 40.0, False)])
        order._deduct_wallet_amount()
        self.assertFalse(order.is_wallet_deducted)
        self.assertEqual(self.partner.wallet_balance, 100.0)
        self.assertFalse(self._transactions(self.partner, 'Debit'))

    def test_change_lines_are_ignored(self):
        order = self._create_order(self.partner, [
            (self.other_pm, 50.0, False),
            (self.wallet_pm, 10.0, True),
        ])
        order._deduct_wallet_amount()
        self.assertEqual(self.partner.wallet_balance, 100.0)
        self.assertFalse(self._transactions(self.partner, 'Debit'))

    def test_skip_when_balance_is_insufficient(self):
        order = self._create_order(self.partner, [(self.wallet_pm, 150.0, False)])
        order._deduct_wallet_amount()
        self.assertEqual(self.partner.wallet_balance, 100.0)
        self.assertFalse(order.is_wallet_deducted)
        self.assertFalse(self._transactions(self.partner, 'Debit'))

    def test_no_double_deduction_when_frontend_already_debited(self):
        # Frontend flow: write_value already created the Debit transaction.
        self.env['res.partner'].write_value(
            60.0, self.partner.id, self.pos_session.id, 40.0, 'USD',
            'FRONTEND-REF')
        order = self._create_order(self.partner, [(self.wallet_pm, 40.0, False)])
        order._deduct_wallet_amount()

        self.assertTrue(order.is_wallet_deducted)
        self.assertEqual(self.partner.wallet_balance, 60.0)
        self.assertEqual(len(self._transactions(self.partner, 'Debit')), 1)

    def test_action_pos_order_paid_triggers_deduction(self):
        order = self._create_order(self.partner, [(self.wallet_pm, 25.0, False)])
        with patch(
            'odoo.addons.point_of_sale.models.pos_order.PosOrder'
            '.action_pos_order_paid', return_value=True,
        ):
            order.action_pos_order_paid()
        self.assertTrue(order.is_wallet_deducted)
        self.assertEqual(self.partner.wallet_balance, 75.0)

    def test_is_wallet_deducted_is_not_copied(self):
        order = self._create_order(self.partner, [(self.wallet_pm, 40.0, False)])
        order.is_wallet_deducted = True
        self.assertFalse(order.copy().is_wallet_deducted)
