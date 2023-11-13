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
from odoo import api, fields, models
import requests, re, json
from datetime import datetime
from dateutil import tz


def remove_html(string):
    regex = re.compile(r'<[^>]+>')
    return regex.sub('', string)


class MailMessage(models.Model):
    _inherit = 'mail.message'
    _description = 'Slack Message'

    is_slack = fields.Boolean(string="Slack", default=False)
    channel = fields.Many2one('mail.channel', string="Channel")

    @api.model
    def create(self, vals):
        """Over-riding the create method to sent message to slack"""
        res = super().create(vals)
        to_zone = tz.gettz('Asia/Kolkata')
        channel_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        company_record = self.env.user.company_id
        channels = self.env['mail.channel'].search([('is_slack', '=', True)])
        for channel in channels:
            msg = self.env['mail.message'].search(
                [('model', '=', 'mail.channel'), ('res_id', '=', channel.id),
                 ('is_slack', '=', False)])
            if msg:
                for rec in msg:
                    payload = {}
                    headers = {
                        'Authorization': 'Bearer ' + company_record.token
                    }
                    new_text = remove_html(rec.body)
                    url = "https://slack.com/api/chat.postMessage?channel=" + rec.record_name + "&" + "text=" + new_text
                    requests.request("POST", url, headers=headers,
                                     data=payload)
                    rec.is_slack = True
                converted_time = datetime.strptime(channel_date,
                                                   '%Y-%m-%d %H:%M:%S').astimezone(
                    to_zone)
                channel.msg_date = converted_time.strftime('%Y-%m-%d %H:%M:%S')
        return res

    def synchronization_slack(self):
        """scheduled action to retrieve message from slack"""
        channel_date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        if self.env.company.slack_sync:
            to_zone = tz.gettz('Asia/Kolkata')
            for channel_id in self.env['mail.channel'].search(
                    [('is_slack', '=', 'true')]):
                company_record = self.env.user.company_id
                payload = {}
                headers = {'Authorization': 'Bearer ' + company_record.token}
                url = "https://slack.com/api/conversations.history?channel=" + channel_id.channel
                channel_response = requests.request("GET", url,
                                                    headers=headers,
                                                    data=payload)
                channels_response = channel_response.__dict__['_content']
                dict_channels = channels_response.decode("UTF-8")
                channels_history = json.loads(dict_channels)
                if channels_history['ok']:
                    channels_history['messages'].reverse()
                    if not channel_id.msg_date:
                        converted_time = datetime.strptime(channel_date,
                                                           '%Y-%m-%d %H:%M:%S').astimezone(
                            to_zone)
                        channel_id.msg_date = converted_time.strftime(
                            '%Y-%m-%d %H:%M:%S')
                    else:
                        for i in channels_history['messages']:
                            if 'user' in i:
                                users = self.env['res.users'].search(
                                    [('slack_user_id', '=', i['user'])])
                                dt_object = (
                                    datetime.fromtimestamp(
                                        float(i['ts'])).strftime(
                                        '%Y-%m-%d %H:%M:%S'))
                                date_time_obj = datetime.strptime(dt_object,
                                                                  '%Y-%m-%d %H:%M:%S')
                                converted_time = date_time_obj.astimezone(
                                    to_zone)
                                if datetime.strptime(converted_time.strftime(
                                        '%Y-%m-%d %H:%M:%S'),
                                        '%Y-%m-%d %H:%M:%S') > channel_id.msg_date:
                                    self.with_user(users.id).create({
                                        'body': i['text'],
                                        'record_name': channel_id.name,
                                        'model': 'mail.channel',
                                        'is_slack': True,
                                        'res_id': channel_id.id,
                                    })
                        converted_time = datetime.strptime(channel_date,
                                                           '%Y-%m-%d %H:%M:%S').astimezone(
                            to_zone)
                        channel_id.msg_date = converted_time.strftime(
                            '%Y-%m-%d %H:%M:%S')
