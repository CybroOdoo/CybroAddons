# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import requests
import logging

from odoo import fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.users'
    _description = 'Slack users'

    slack_user_id = fields.Char(string="Slack User ID", readonly=True)
    is_slack_internal_users = fields.Boolean("Slack User", default=False)

    def sync_users(self):
        """To load slack users"""
        slack_internal_user_list = [user_id.slack_user_id for user_id in self]
        url = "https://slack.com/api/users.list"
        company_record = self.env.user.company_id
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + company_record.token
        }
        logger = logging.getLogger(__name__)
        try:
            response = requests.get(url, headers=headers, data=payload)
            response.raise_for_status()
            users = response.json()
        except requests.exceptions.RequestException as err:
            # Handle request exceptions
            logger.error(f"Error during Slack API request: {err}")
            return
        members = users.get('members', False)
        if members is not False:
            vals_list = []
            for rec in members:
                if 'is_email_confirmed' in rec and rec['is_email_confirmed'] is True and 'email' in rec['profile']:
                    email = rec['profile']['email']
                    if rec['id'] not in slack_internal_user_list:
                        vals = {
                            'name': rec['real_name'],
                            'slack_user_id': rec['id'],
                            'is_slack_internal_users': True,
                            'login': email,
                        }
                        vals_list.append(vals)
            try:
                if vals_list:
                    for val in vals_list:
                        existing_user = self.search([
                            ('login', '=', val['login'])], limit=1)
                        if existing_user:
                            if existing_user.is_slack_internal_users:
                                existing_user.write(
                                    {'slack_user_id': val['slack_user_id']})
                            else:
                                raise UserError("User with email '%s' already exists as a Slack user." % val['login'])
                        else:
                            self.create(val)
            except Exception as e:
                # Handle creation exception
                logger.error(f"Error creating Slack users: {e}")
                return
