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
import logging
import requests
from odoo import fields, models
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Inherited to add more field and functions"""
    _inherit = 'res.company'

    bot_token = fields.Char(required=True, string="BOT Token",
                        help="Bot Token used to send messages from Odoo to Slack on behalf of non-admin users. "
                             "This ensures messages are posted with the correct user identity instead of "
                             "appearing under the admin account.")
    slack_users_ids = fields.One2many('slack.user',
                                      'res_company_id',
                                      string="All Users",
                                      help="All Slack Users")
    slack_channel_ids = fields.One2many('slack.channel',
                                        'res_company_id',
                                        string="Channels",
                                        help="All Slack channels")
    slack_sync = fields.Boolean(string="Is Slack",
                                help="True if connected to Slack")

    def action_sync(self):
        """To sync channels and members from slack"""
        url_users = "https://slack.com/api/users.list"
        url_channels = "https://slack.com/api/conversations.list"
        headers = {
            "Authorization": f"Bearer {self.bot_token}"
        }
        # --- Fetch users ---
        response = requests.get(url_users, headers=headers)
        data = response.json()
        if not data.get("ok"):
            raise UserError(f"Slack API Error: {data.get('error')}")
        members = data.get("members", [])
        # --- Fetch channels ---
        channels_response = requests.get(url_channels, headers=headers)
        channels = channels_response.json()
        # --- Pre-fetch records to avoid repeated DB hits ---
        discuss_channel = self.env['discuss.channel']
        # --- Sync members to channels ---
        synced_channels = discuss_channel.search([('is_slack', '=', True)])
        existing_channel_ids = synced_channels.mapped('channel')
        # --- Create missing channels ---
        for channel in channels.get('channels', []):
            if channel['id'] not in existing_channel_ids:
                new_channel = discuss_channel.create({
                    'name': channel['name'],
                    'channel': channel['id'],
                    'is_slack': True,
                    'group_public_id': []
                })
                synced_channels |= new_channel
        # --- Sync users ---
        self.env.user.action_sync_users(members)
        # --- Prepare existing data sets ---
        existing_slack_channel_names = set(self.slack_channel_ids.mapped('name'))
        existing_company_users = set(self.env.user.company_id.slack_users_ids.mapped('user'))
        users_list = []
        channels_list = []
        # --- Channels mapping ---
        for channel in channels.get('channels', []):
            if channel['name'] not in existing_slack_channel_names:
                channels_list.append((0, 0, {
                    'name': channel['name']
                }))
        self.slack_channel_ids = channels_list
        # --- Users mapping ---
        for rec in members:
            if rec.get('deleted'):
                continue
            profile = rec.get('profile', {})
            email = profile.get('email') or rec.get('real_name') or ''
            # Add to slack users list (company)
            if rec['id'] not in existing_company_users:
                users_list.append((0, 0, {
                    'name': rec.get('real_name'),
                    'user': rec['id'],
                    'email': email,
                }))
        synced_channels.action_sync_members()
        self.slack_users_ids = users_list
        self.slack_sync = True
