# -*- coding: utf-8 -*-
#############################################################################
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
from odoo import api, models
from odoo.fields import Command


class ResUsers(models.Model):
    """Extends users with Oil Admin group synchronization rules."""
    _inherit = "res.users"

    def _sync_oil_admin_account_group(self):
        """Automatically assign the Account User group to users in
         the Oil Admin group."""
        if self.env.context.get("skip_oil_admin_account_sync"):
            return

        oil_admin_group = self.env.ref("oil_erp_base.group_oil_admin",
                                       raise_if_not_found=False)
        account_user_group = self.env.ref("account.group_account_user",
                                          raise_if_not_found=False)
        if not oil_admin_group or not account_user_group:
            return

        users_to_update = self.filtered(
            lambda
                user: oil_admin_group in user.all_group_ids and account_user_group not in user.all_group_ids
        )
        if users_to_update:
            users_to_update.with_context(
                skip_oil_admin_account_sync=True).write({
                "group_ids": [Command.link(account_user_group.id)],
            })

    @api.model_create_multi
    def create(self, vals_list):
        """Create users and sync Oil Admin group with Account User group."""
        users = super().create(vals_list)
        users._sync_oil_admin_account_group()
        return users

    def write(self, vals):
        """Update users and re-sync group assignments if group_ids are modified."""
        result = super().write(vals)
        if "group_ids" in vals:
            self._sync_oil_admin_account_group()
        return result
