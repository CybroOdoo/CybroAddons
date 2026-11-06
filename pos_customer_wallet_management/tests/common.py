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
from odoo.tests.common import TransactionCase, new_test_user


class WalletCommon(TransactionCase):
    """Shared fixtures for the wallet module tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wallet_journal = cls.env.ref(
            'pos_customer_wallet_management.pos_wallet_journal_main')
        cls.wallet_pm = cls.env.ref(
            'pos_customer_wallet_management.pos_wallet_payment_method_main')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Wallet Test Customer',
            'wallet_balance': 100.0,
        })

    @classmethod
    def _setup_pos(cls):
        """Create a POS config with the wallet payment method and an opened
        session owned by a dedicated user (avoids the one-open-session-per-user
        constraint)."""
        cls.pos_user = new_test_user(
            cls.env, login='wallet_pos_user',
            groups='base.group_user,point_of_sale.group_pos_user')
        # A second, non-wallet payment method. It must belong to the config,
        # otherwise pos.payment rejects it ("payment method not allowed").
        # A bank type is used so that opening the session needs no cash
        # statement.
        other_journal = cls.env['account.journal'].create({
            'name': 'Wallet Test Bank',
            'type': 'bank',
            'code': 'WTBNK',
        })
        cls.other_pm = cls.env['pos.payment.method'].create({
            'name': 'Wallet Test Other',
            'type': 'bank',
            'journal_id': other_journal.id,
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Wallet Test POS',
            'payment_method_ids': [
                Command.set([cls.wallet_pm.id, cls.other_pm.id])],
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
            'user_id': cls.pos_user.id,
        })
        cls.pos_session.set_opening_control(0, '')

    def _create_order(self, partner, payments, partner_less=False):
        """Create a pos.order with the given payments.

        :param payments: list of (payment_method, amount, is_change)
        """
        total = sum(amount for _pm, amount, is_change in payments
                    if not is_change)
        order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'partner_id': False if partner_less else partner.id,
            'amount_tax': 0.0,
            'amount_total': total,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        for method, amount, is_change in payments:
            self.env['pos.payment'].create({
                'pos_order_id': order.id,
                'payment_method_id': method.id,
                'amount': amount,
                'is_change': is_change,
            })
        return order

    def _transactions(self, partner, tx_type=None):
        domain = [('customer', '=', partner.name)]
        if tx_type:
            domain.append(('type', '=', tx_type))
        return self.env['wallet.transaction'].search(domain)
