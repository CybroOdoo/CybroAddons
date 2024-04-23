# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import logging
import requests
from requests import RequestException
from odoo import fields, models


class DiscussChannel(models.Model):
    """Inherited to add more field and functions"""
    _inherit = 'discuss.channel'

    is_slack = fields.Boolean(string="Slack", help="True for Slack connected")
    channel = fields.Char(string="Slack Reference",
                          help='Slack reference of channel')
    msg_date = fields.Datetime(string="Message Date", help="Date of message")

    def action_sync_members(self):
        """To load members into channels"""
        headers = {
            'Authorization': 'Bearer ' + self.env.user.company_id.token
        }
        logger = logging.getLogger(__name__)
        for channel in self:
            if not channel.is_slack:
                continue
            try:
                url = "https://slack.com/api/conversations.members?channel=" + channel.channel
                with requests.Session() as session:
                    response = session.get(url, headers=headers, data={})
                    slack_user_list = []
                    for slack_user_ref in response.json()['members']:
                        contact = self.env['res.partner'].search(
                            [('slack_user_ref', '=', slack_user_ref)])
                        if not contact:
                            contact = self.env['res.partner'].create({
                                'name': 'Slack User',
                                'slack_user_ref': slack_user_ref
                            })
                        slack_user_list.append(contact.id)
                    channel_user_list = channel.channel_member_ids.mapped(
                        'partner_id.id')
                    channel.channel_member_ids = [
                        (0, 0, {'partner_id': contact_id})
                        for contact_id in slack_user_list
                        if contact_id not in channel_user_list
                    ]
            except RequestException as e:
                # Handle request exception
                logger.error(f"Error occurred during API request: {str(e)}")
            except (KeyError, ValueError) as e:
                # Handle JSON parsing or key error
                logger.error(
                    f"Error occurred while parsing API response: {str(e)}")
            except Exception as e:
                # Handle any other exceptions
                logger.error(f"An error occurred: {str(e)}")
