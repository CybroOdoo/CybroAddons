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

from odoo.tests import tagged

from .common import WalletCommon


@tagged('post_install', '-at_install')
class TestResPartner(WalletCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_pos()

    def test_wallet_balance_default_is_zero(self):
        partner = self.env['res.partner'].create({'name': 'Fresh Wallet User'})
        self.assertEqual(partner.wallet_balance, 0.0)

    def test_wallet_count(self):
        self.assertEqual(self.partner.wallet_count, 0)
        self.env['wallet.transaction'].create([
            {'type': 'Credit', 'customer': self.partner.name, 'amount': 5.0},
            {'type': 'Debit', 'customer': self.partner.name, 'amount': 2.0},
        ])
        # wallet_count is a non-stored compute without dependencies, so the
        # cached value must be dropped before reading it again.
        self.partner.invalidate_recordset(['wallet_count'])
        self.assertEqual(self.partner.wallet_count, 2)

    def test_action_number_of_wallet(self):
        action = self.partner.action_number_of_wallet()
        self.assertEqual(action['res_model'], 'wallet.transaction')
        self.assertEqual(action['domain'],
                         [('customer', '=', self.partner.name)])

    def test_action_recharge_opens_wizard(self):
        action = self.partner.action_recharge()
        self.assertEqual(action['res_model'], 'recharge.wallet')
        self.assertEqual(action['target'], 'new')

    def test_load_pos_data_fields_contains_wallet_balance(self):
        fields_list = self.env['res.partner']._load_pos_data_fields(
            self.pos_config)
        self.assertIn('wallet_balance', fields_list)

    def test_write_value_unknown_partner(self):
        result = self.env['res.partner'].write_value(
            50.0, 999999999, self.pos_session.id, 50.0, 'USD', 'REF-X')
        self.assertFalse(result)

    def test_write_value_creates_debit_and_updates_balance(self):
        result = self.env['res.partner'].write_value(
            60.0, self.partner.id, self.pos_session.id, 40.0, 'USD',
            'REF-001')
        self.assertEqual(result, 60.0)
        self.assertEqual(self.partner.wallet_balance, 60.0)
        debit = self._transactions(self.partner, 'Debit')
        self.assertEqual(len(debit), 1)
        self.assertEqual(debit.amount, 40.0)
        self.assertEqual(debit.pos_order, 'REF-001')
        self.assertEqual(debit.currency, 'USD')

    def test_write_value_duplicate_order_ref_is_ignored(self):
        Partner = self.env['res.partner']
        Partner.write_value(
            60.0, self.partner.id, self.pos_session.id, 40.0, 'USD',
            'REF-DUP')
        result = Partner.write_value(
            10.0, self.partner.id, self.pos_session.id, 50.0, 'USD',
            'REF-DUP')
        # Second call returns the current balance and changes nothing.
        self.assertEqual(result, 60.0)
        self.assertEqual(self.partner.wallet_balance, 60.0)
        self.assertEqual(len(self._transactions(self.partner, 'Debit')), 1)

    def test_write_value_without_order_ref_uses_session_label(self):
        self.env['res.partner'].write_value(
            90.0, self.partner.id, self.pos_session.id, 10.0, 'USD')
        debit = self._transactions(self.partner, 'Debit')
        self.assertEqual(len(debit), 1)
        self.assertTrue(debit.pos_order)

    def test_write_value_marks_pos_order_as_deducted(self):
        order = self._create_order(self.partner, [(self.wallet_pm, 30.0, False)])
        self.assertFalse(order.is_wallet_deducted)
        self.env['res.partner'].write_value(
            70.0, self.partner.id, self.pos_session.id, 30.0, 'USD',
            order.uuid)
        self.assertTrue(order.is_wallet_deducted)
