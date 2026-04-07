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
from . import models
from . import wizard


def post_init_hook(env):
    """
    Force-activate the Wallet journal and payment method after installation,
    in case they were previously archived by the uninstall hook.
    """
    journal = env.ref(
        'pos_customer_wallet_management.pos_wallet_journal_main',
        raise_if_not_found=False)
    if journal and not journal.active:
        journal.with_context(active_test=False).write({'active': True})

    payment_method = env.ref(
        'pos_customer_wallet_management.pos_wallet_payment_method_main',
        raise_if_not_found=False)
    if payment_method and not payment_method.active:
        payment_method.with_context(active_test=False).write({'active': True})


def uninstall_hook(env):
    """
    Archive Wallet payment method and journal when module is uninstalled.
    """
    payment_method = env.ref(
        'pos_customer_wallet_management.pos_wallet_payment_method_main',
        raise_if_not_found=False)
    if payment_method:
        # Remove from POS configs first to prevent FK errors
        configs = env['pos.config'].search(
            [('payment_method_ids', 'in', payment_method.id)])
        for config in configs:
            config.payment_method_ids = [(3, payment_method.id)]
        payment_method.active = False

    journal = env.ref(
        'pos_customer_wallet_management.pos_wallet_journal_main',
        raise_if_not_found=False)
    if journal:
        journal.active = False
