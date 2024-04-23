# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
from odoo import fields, models
from odoo.exceptions import UserError


class ResUsers(models.Model):
    """Inherited to add more field and functions"""
    _inherit = 'res.users'

    slack_user_ref = fields.Char(string="Slack User ID",
                                 help="Slack User reference of user",
                                 readonly=True)
    is_slack_internal_users = fields.Boolean(string="Slack User",
                                             help="True for Slack internal"
                                                  " users")

    def action_sync_users(self):
        """To load slack users"""
        slack_internal_user_list = [user_id.slack_user_ref for user_id in self]
        headers = {
            'Authorization': 'Bearer ' + self.env.user.company_id.token
        }
        logger = logging.getLogger(__name__)
        try:
            response = requests.get("https://slack.com/api/users.list",
                                    headers=headers, data={})
            response.raise_for_status()
        except requests.exceptions.RequestException as err:
            # Handle request exceptions
            logger.error(f"Error during Slack API request: {err}")
            return
        if response.json().get('members', False) is not False:
            vals_list = []
            for rec in response.json().get('members', False):
                if ('is_email_confirmed' in rec and
                        rec['is_email_confirmed'] is True and
                        'email' in rec['profile']):
                    if rec['id'] not in slack_internal_user_list:
                        vals = {
                            'name': rec['real_name'],
                            'slack_user_ref': rec['id'],
                            'is_slack_internal_users': True,
                            'login': rec['profile']['email'],
                        }
                        vals_list.append(vals)
            try:
                for val in vals_list:
                    existing_user = self.search([
                        ('login', '=', val['login'])], limit=1)
                    if existing_user:
                        if existing_user.is_slack_internal_users:
                            existing_user.write(
                                {'slack_user_ref': val['slack_user_ref']})
                        else:
                            raise UserError(
                                "User with email '%s' already exists as a"
                                " Slack user." %
                                val['login'])
                    else:
                        self.create(val)
            except Exception as e:
                # Handle creation exception
                logger.error(f"Error creating Slack users: {e}")
                return
