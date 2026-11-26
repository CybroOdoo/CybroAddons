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
"""Chief Accountant no longer implies Administrator.

``security/security.xml`` is a ``noupdate`` file and made Chief Accountant and
Administrator imply each other, so every Chief Accountant was an
Administrator. Remove Administrator from Chief Accountant's implied groups;
Chief Accountant keeps implying Accountant, and Administrator keeps implying
Chief Accountant (core ladder: Invoicing < Accountant < Chief < Administrator).
"""
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    chief = env.ref('base_accounting_kit.group_account_chief',
                    raise_if_not_found=False)
    manager = env.ref('account.group_account_manager',
                      raise_if_not_found=False)
    if not chief or not manager or manager not in chief.implied_ids:
        return
    chief.write({'implied_ids': [(3, manager.id),
                                 (4, env.ref('account.group_account_user').id)]})
    env.invalidate_all()
    only_chief = chief.user_ids.filtered(
        lambda u: manager not in u.all_group_ids)
    _logger.warning(
        "Chief Accountant no longer implies Administrator. %d user(s) are "
        "Chief Accountant without being Administrator: %s",
        len(only_chief), ', '.join(only_chief.mapped('login')))
