# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import requests
import logging
from odoo import fields, models, Command
from odoo.exceptions import UserError


class ResUsers(models.Model):
    """Inherited to add more field and functions"""
    _inherit = 'res.users'

    slack_user_ref = fields.Char(string="Slack User ID",
                                 help="Slack User reference of user",
                                 readonly=True, copy=False)
    is_slack_internal_users = fields.Boolean(string="Slack User",
                                             help="True for Slack internal"
                                                  " users", copy=False)

    def action_sync_users(self, members):
        """To load slack users"""
        logger = logging.getLogger(__name__)
        users_model = self.env['res.users']
        # Existing slack user refs
        slack_internal_user_list = set(self.search([]).mapped('slack_user_ref'))
        if members:
            vals_list = []
            for rec in members:
                profile = rec.get('profile', {})
                if rec.get('is_email_confirmed'):
                    if rec['id'] not in slack_internal_user_list:
                        vals = {
                            'name': rec.get('real_name'),
                            'slack_user_ref': rec['id'],
                            'is_slack_internal_users': True,
                            'login': profile.get('email') or rec.get('real_name') or '',
                            'company_ids': [Command.link(self.env.company.id)],
                            'company_id': self.env.company.id
                        }
                        vals_list.append(vals)
            try:
                if not vals_list:
                    return
                # Prefetch existing users by login (avoid search per loop)
                logins = [val['login'] for val in vals_list]
                existing_users = users_model.search([('login', 'in', logins)])
                user_map = {user.login: user for user in existing_users}
                for val in vals_list:
                    existing_user = user_map.get(val['login'])
                    if existing_user:
                        if existing_user.is_slack_internal_users:
                            existing_user.write({
                                'slack_user_ref': val['slack_user_ref']
                            })
                        else:
                            raise UserError(
                                "User with email '%s' already exists as a Slack user." % val['login']
                            )
                    else:
                        users_model.create(val)
            except Exception as e:
                logger.error(f"Error creating Slack users: {e}")
                return
