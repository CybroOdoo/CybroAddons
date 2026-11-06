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
class TestWalletTransaction(WalletCommon):

    def test_sequence_is_assigned_on_create(self):
        tx = self.env['wallet.transaction'].create([{
            'type': 'Credit',
            'customer': self.partner.name,
            'amount': 10.0,
        }])
        self.assertTrue(tx.name)
        self.assertTrue(tx.name.startswith('WT'))

    def test_sequence_increments_for_each_record(self):
        txs = self.env['wallet.transaction'].create([
            {'type': 'Credit', 'customer': self.partner.name, 'amount': 1.0},
            {'type': 'Debit', 'customer': self.partner.name, 'amount': 2.0},
        ])
        self.assertEqual(len(txs), 2)
        self.assertNotEqual(txs[0].name, txs[1].name)

    def test_fields_are_stored(self):
        tx = self.env['wallet.transaction'].create([{
            'type': 'Debit',
            'customer': self.partner.name,
            'pos_order': 'Order/0001',
            'amount': 25.5,
            'currency': 'USD',
        }])
        self.assertEqual(tx.type, 'Debit')
        self.assertEqual(tx.customer, self.partner.name)
        self.assertEqual(tx.pos_order, 'Order/0001')
        self.assertAlmostEqual(tx.amount, 25.5)
        self.assertEqual(tx.currency, 'USD')
