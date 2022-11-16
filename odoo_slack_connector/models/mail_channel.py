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


import requests, json
from odoo import models, fields


class MailChannel(models.Model):
    _inherit = 'mail.channel'
    _description = 'Slack Channel'

    is_slack = fields.Boolean("Slack", default=False)
    channel = fields.Char("ID")
    msg_date = fields.Datetime()

    def sync_members(self):
        """To load members into channels"""
        company_record = self.env.user.company_id
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + company_record.token
        }
        for channels in self:
            slack_user_list = []
            sample_list = []
            slack_user_list.clear()
            current_channel_user_list = []
            current_channel_user_list.clear()

            if channels.is_slack:
                url = "https://slack.com/api/conversations.members?channel=" + channels.channel
                channel_member_resonse = requests.request("GET", url,
                                                          headers=headers,
                                                          data=payload)
                channel_members = channel_member_resonse.__dict__['_content']
                dict_channel_members = channel_members.decode("UTF-8")
                channel_member = json.loads(dict_channel_members)
                for slack_user_id in channel_member['members']:
                    contact = self.env['res.partner'].search(
                        [('slack_user_id', '=', slack_user_id)])
                    slack_user_list.append(contact.id)
                for last_seen_partner_ids in channels.channel_last_seen_partner_ids:
                    current_channel_user_list.append(
                        last_seen_partner_ids.partner_id.id)
                for contact_id in slack_user_list:
                    if contact_id not in current_channel_user_list:
                        sample_list.append((0, 0, {'partner_id': contact_id}))
                channels.channel_last_seen_partner_ids = sample_list
