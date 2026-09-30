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
from odoo import _, fields, models

class GitHubConfig(models.Model):
    """
    Manages GitHub API authentication and configuration settings.
    """
    _name = 'github.config'
    _description = 'GitHub Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Configuration Name', required=True, default='GitHub', help="Name for this configuration.")
    active = fields.Boolean('Active', default=True, help="Whether this configuration is currently active.")
    access_token = fields.Char('Access Token', required=True, help='GitHub Personal Access Token')
    username = fields.Char('GitHub Username', help='Your GitHub username or organization')

    def action_test_connection(self):
        """
        Tests the connection to GitHub API using the provided access token.
        """
        import requests
        from odoo.exceptions import UserError
        try:
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            response = requests.get('https://api.github.com/user', headers=headers)
            response.raise_for_status()
            data = response.json()
            if self.username and data.get('login').lower() != self.username.lower():
                raise UserError(_("Token is valid, but belongs to user '%s', not '%s'.") % (data.get('login'), self.username))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test'),
                    'message': _('Connection Successful! Authenticated as %s.') % data.get('login'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))
