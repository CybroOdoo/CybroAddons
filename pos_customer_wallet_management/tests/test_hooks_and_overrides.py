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

from odoo import Command
from odoo.addons.pos_customer_wallet_management import (
    post_init_hook,
    uninstall_hook,
)
from odoo.tests import tagged

from .common import WalletCommon


@tagged('post_install', '-at_install')
class TestHooksAndOverrides(WalletCommon):
    """Data records and write overrides (needs an open session)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_pos()

    # -- data ---------------------------------------------------------
    def test_data_records_exist(self):
        self.assertTrue(self.wallet_journal.is_wallet_journal)
        self.assertEqual(self.wallet_journal.code, 'WLT')
        self.assertEqual(self.wallet_pm.journal_id, self.wallet_journal)
        self.assertTrue(self.wallet_pm.is_wallet_journal)
        self.assertTrue(self.env['ir.sequence'].search_count(
            [('code', '=', 'wallet.transaction')]))

    def test_non_wallet_payment_method_flag(self):
        self.assertFalse(self.other_pm.is_wallet_journal)

    def test_load_pos_data_fields_contains_wallet_flag(self):
        fields_list = self.env['pos.payment.method']._load_pos_data_fields(
            self.pos_config)
        self.assertIn('is_wallet_journal', fields_list)

    # -- write overrides ---------------------------------------------
    def test_journal_write_with_unchanged_values(self):
        res = self.wallet_journal.write({
            'name': self.wallet_journal.name,
            'is_wallet_journal': True,
        })
        self.assertTrue(res)
        self.assertEqual(self.wallet_journal.name, 'POS Wallet')

    def test_journal_write_with_changed_values(self):
        self.wallet_journal.write({'name': 'POS Wallet Renamed'})
        self.assertEqual(self.wallet_journal.name, 'POS Wallet Renamed')

    def test_payment_method_write_unchanged_value_with_open_session(self):
        self.assertTrue(self.wallet_pm.open_session_ids)
        res = self.wallet_pm.write({'journal_id': self.wallet_pm.journal_id.id})
        self.assertTrue(res)

    def test_payment_method_write_without_open_session(self):
        journal = self.env['account.journal'].create({
            'name': 'Wallet Test Bank 2',
            'type': 'bank',
            'code': 'WTBK2',
        })
        method = self.env['pos.payment.method'].create({
            'name': 'Wallet Test Free',
            'type': 'bank',
            'journal_id': journal.id,
        })
        self.assertFalse(method.open_session_ids)
        res = method.write({'name': 'Wallet Test Free 2'})
        self.assertTrue(res)
        self.assertEqual(method.name, 'Wallet Test Free 2')


@tagged('post_install', '-at_install')
class TestWalletHooks(WalletCommon):
    """Install/uninstall hooks (must run without any open session, since
    Odoo refuses to remove a payment method from a config in use)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hook_config = cls.env['pos.config'].create({
            'name': 'Wallet Hook POS',
            'payment_method_ids': [Command.set([cls.wallet_pm.id])],
        })

    def test_uninstall_hook_archives_wallet_records(self):
        uninstall_hook(self.env)
        self.assertFalse(self.wallet_pm.active)
        self.assertFalse(self.wallet_journal.active)
        self.assertNotIn(self.wallet_pm, self.hook_config.payment_method_ids)

    def test_post_init_hook_reactivates_wallet_records(self):
        uninstall_hook(self.env)
        post_init_hook(self.env)
        self.assertTrue(self.wallet_pm.active)
        self.assertTrue(self.wallet_journal.active)
