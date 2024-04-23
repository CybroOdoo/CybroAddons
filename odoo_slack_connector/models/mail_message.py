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
import re
import requests
from datetime import datetime
from dateutil import tz
from odoo import api, fields, models


def remove_html(string):
    regex = re.compile(r'<[^>]+>')
    return regex.sub('', string)


class MailMessage(models.Model):
    """Inherited to add more field and functions"""
    _inherit = 'mail.message'

    is_slack = fields.Boolean(string="Slack",
                              help="True for Slack connected messages")
    channel = fields.Many2one('discuss.channel', string="Channel",
                              help="Channel corresponds to the message")

    @api.model
    def create(self, vals):
        """Over-riding the create method to sent message to slack"""
        res = super().create(vals)
        channels = self.env['discuss.channel'].search([('is_slack', '=', True)])
        for channel in channels:
            msg = self.env['mail.message'].search(
                [('model', '=', 'discuss.channel'), ('res_id', '=', channel.id),
                 ('is_slack', '=', False)])
            if msg:
                for rec in msg:
                    headers = {
                        'Authorization': 'Bearer ' +
                                         self.env.user.company_id.token
                    }
                    url = ("https://slack.com/api/chat.postMessage?channel=" +
                           rec.record_name + "&" + "text=" + remove_html(
                                rec.body))
                    requests.request("POST", url, headers=headers,
                                     data={})
                    rec.is_slack = True
                converted_time = datetime.strptime(
                    datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                    '%Y-%m-%d %H:%M:%S').astimezone(
                    tz.gettz('Asia/Kolkata'))
                channel.msg_date = converted_time.strftime('%Y-%m-%d %H:%M:%S')
        return res

    def action_synchronization_slack(self):
        """scheduled action to retrieve message from slack"""
        if self.env.company.slack_sync:
            for channel_id in self.env['discuss.channel'].search(
                    [('is_slack', '=', 'true')]):
                headers = {'Authorization': 'Bearer ' +
                                            self.env.user.company_id.token}
                url = ("https://slack.com/api/conversations.history?channel=" +
                       channel_id.channel)
                channels_history = json.loads(requests.request("GET", url,
                                                               headers=headers,
                                                               data={

                                                               }).__dict__[
                                                  '_content'].decode("UTF-8"))
                if channels_history['ok']:
                    channels_history['messages'].reverse()
                    if not channel_id.msg_date:
                        converted_time = datetime.strptime(
                            datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                            '%Y-%m-%d %H:%M:%S').astimezone(
                            tz.gettz('Asia/Kolkata'))
                        channel_id.msg_date = converted_time.strftime(
                            '%Y-%m-%d %H:%M:%S')
                    else:
                        for item in channels_history['messages']:
                            if 'user' in item:
                                users = self.env['res.users'].search(
                                    [('slack_user_ref', '=', item['user'])])
                                dt_object = (
                                    datetime.fromtimestamp(
                                        float(item['ts'])).strftime(
                                        '%Y-%m-%d %H:%M:%S'))
                                date_time_obj = datetime.strptime(
                                    dt_object, '%Y-%m-%d %H:%M:%S')
                                converted_time = date_time_obj.astimezone(
                                    tz.gettz('Asia/Kolkata'))
                                if (datetime.strptime(converted_time.strftime(
                                        '%Y-%m-%d %H:%M:%S'),
                                        '%Y-%m-%d %H:%M:%S') >
                                        channel_id.msg_date):
                                    self.with_user(users.id).create({
                                        'body': item['text'],
                                        'record_name': channel_id.name,
                                        'model': 'discuss.channel',
                                        'is_slack': True,
                                        'res_id': channel_id.id,
                                    })
                        converted_time = datetime.strptime(
                            datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
                            '%Y-%m-%d %H:%M:%S').astimezone(
                            tz.gettz('Asia/Kolkata'))
                        channel_id.msg_date = converted_time.strftime(
                            '%Y-%m-%d %H:%M:%S')
