# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
import requests

from odoo import fields, models
from odoo.exceptions import UserError


class GitHubConfig(models.Model):
    """
    Model for storing GitHub configuration and authentication details.
    """
    _name = 'github.config'
    _description = 'GitHub Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        'Configuration Name', required=True, default='GitHub',
        help='The name of the configuration setting.')
    active = fields.Boolean(
        default=True,
        help='Specify if this configuration is active.')
    access_token = fields.Char(
        required=True, help='GitHub Personal Access Token')
    username = fields.Char(
        'GitHub Username', help='Your GitHub username or organization')

    def action_test_connection(self):
        """
        Test the connection to GitHub using the provided access token.
        :return: Notification action indicating success or failure.
        """
        try:
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/user', headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if self.username and data.get('login').lower() != self.username.lower():
                raise UserError(self.env._(
                    "Token is valid, but belongs to user '%(token_user)s', not '%(expected_user)s'.",
                    token_user=data.get('login'),
                    expected_user=self.username,
                ))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': self.env._('Connection Test'),
                    'message': self.env._('Connection Successful! Authenticated as %s.', data.get('login')),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(self.env._("Connection failed: %s", str(e)))
