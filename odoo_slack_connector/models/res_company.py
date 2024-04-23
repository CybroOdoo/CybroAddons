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
import json
import logging
import requests
from odoo import fields, models

logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Inherited to add more field and functions"""
    _inherit = 'res.company'

    token = fields.Char(required=True, string="Slack Token",
                        help="Token for connecting with Slack")
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
        self.slack_sync = True
        url1 = "https://slack.com/api/users.list"
        url2 = "https://slack.com/api/conversations.list"
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        users = json.loads(requests.request("GET", url1,
                                            headers=headers,
                                            data={}).__dict__[
                               '_content'].decode("UTF-8"))
        members = users.get('members', False)
        channels = json.loads(requests.request("GET", url2,
                                               headers=headers,
                                               data={}).__dict__[
                                  '_content'].decode("UTF-8"))
        search_channel = self.env['discuss.channel'].search([])
        for channel in channels['channels']:
            if channel['id'] not in search_channel.mapped('channel'):
                self.env['discuss.channel'].create([
                    {
                        'name': channel['name'],
                        'channel': channel['id'],
                        'is_slack': True,
                    }, ])
        search_channel.action_sync_members()
        self.env['res.users'].search([]).action_sync_users()
        users_list = []
        channels_list = []
        for channel in channels['channels']:
            if channel['name'] not in self.slack_channel_ids.mapped('name'):
                channels_list.append((0, 0,
                                      {'name': channel['name']}
                                      ))
        self.slack_channel_ids = channels_list
        if members is not False:
            for rec in members:
                if 'email' in rec['profile']:
                    email = rec['profile']['email']
                else:
                    email = ''
                if (not rec['deleted'] and rec['id'] not in
                        self.env.user.company_id.slack_users_ids.mapped(
                            'user')):
                    users_list.append((0, 0,
                                       {'name': rec['real_name'],
                                        'user': rec['id'],
                                        'email': email},
                                       ))
        self.slack_users_ids = users_list
        if members is not False:
            for rec in members:
                if 'email' in rec['profile']:
                    email = rec['profile']['email']
                else:
                    email = ''
                if (not rec['deleted'] and rec['id'] not in
                        self.env['res.partner'].search([
                        ]).mapped('slack_user_ref')):
                    self.env['res.partner'].create({
                        'name': rec['real_name'],
                        'slack_user_ref': rec['id'],
                        'is_slack_user': True,
                        'email': email
                    })
