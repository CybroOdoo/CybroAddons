# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import json
import logging
import requests
from requests import RequestException
from odoo import fields, models

logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Slack Api'

    token = fields.Char(required=True, string="Slack Token")
    slack_users_ids = fields.One2many('res.company.slack.users',
                                      'res_company_id',
                                      "All Users")
    slack_channel_ids = fields.One2many('res.company.slack.channels',
                                        'res_company_id',
                                        "Channels")
    slack_sync = fields.Boolean(default=False)

    def sync_conversations(self):
        """To sync channels and members from slack"""
        self.slack_sync = True
        url1 = "https://slack.com/api/users.list"
        url2 = "https://slack.com/api/conversations.list"
        url3 = "https://slack.com/api/users.info?user="

        payload = {}
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        users_response = requests.request("GET", url1, headers=headers,
                                          data=payload)
        users_response = users_response.__dict__['_content']
        dict_users = users_response.decode("UTF-8")
        users = json.loads(dict_users)
        members = users.get('members', False)
        channel_list = []
        channel_response = requests.request("GET", url2, headers=headers,
                                            data=payload)
        channels_response = channel_response.__dict__['_content']
        dict_channels = channels_response.decode("UTF-8")
        channels = json.loads(dict_channels)
        search_channel = self.env['mail.channel'].search([])
        for i in search_channel:
            channel_list.append(i.channel)
        for channel in channels['channels']:
            if channel['id'] not in channel_list:
                self.env['mail.channel'].create([
                    {
                        'name': channel['name'],
                        'channel': channel['id'],
                        'is_slack': True,
                    }, ])
        search_channel.sync_members()
        users = self.env['res.users'].search([])
        users.sync_users()
        users_list = []
        slack_id_list = []
        channels_list = []
        record_channel_list = []
        record = self.env.user.company_id
        for in_channel in self.slack_channel_ids:
            record_channel_list.append(in_channel.name)
        for channel in channels['channels']:
            if channel['name'] not in record_channel_list:
                channels_list.append((0, 0,
                                      {'name': channel['name']}
                                      ))
        self.slack_channel_ids = channels_list
        record_user_list = []
        for rec in record.slack_users_ids:
            record_user_list.append(rec.user)
        if members is not False:
            for rec in members:
                if 'email' in rec['profile']:
                    email = rec['profile']['email']
                else:
                    email = ''
                if rec['id'] not in record_user_list:
                    users_list.append((0, 0,
                                       {'name': rec['real_name'],
                                        'user': rec['id'],
                                        'email': email},
                                       ))
        self.slack_users_ids = users_list
        for partner_id in self.env['res.partner'].search([]):
            slack_id_list.append(partner_id.slack_user_id)
        if members is not False:
            for rec in members:
                if 'email' in rec['profile']:
                    email = rec['profile']['email']
                else:
                    email = ''
                if rec['id'] not in slack_id_list:
                    vals = {
                        'name': rec['real_name'],
                        'slack_user_id': rec['id'],
                        'is_slack_user': True,
                        'email': email
                    }
                    self.env['res.partner'].create(vals)


class SlackUsersLines(models.Model):
    _name = 'res.company.slack.users'
    _description = 'Slack users'

    name = fields.Char(string="Name")
    email = fields.Char(string="Email")
    user = fields.Char(string="User ID")
    res_company_id = fields.Many2one("res.company")


class SlackChannelLines(models.Model):
    _name = 'res.company.slack.channels'
    _description = 'Slack Channels'

    name = fields.Char(string="Name")
    res_company_id = fields.Many2one("res.company")
