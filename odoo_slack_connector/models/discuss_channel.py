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
from requests import RequestException
from odoo import fields, models, Command


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
            'Authorization': 'Bearer ' + self.env.user.company_id.bot_token
        }
        logger = logging.getLogger(__name__)
        res_users = self.env['res.users']
        # Create one session for all channels (instead of per loop)
        with requests.Session() as session:
            for channel in self:
                if not channel.is_slack:
                    continue
                try:
                    # for joining bot in public channel, for Private channel, bot must be added as a member
                    join_url = 'https://slack.com/api/conversations.join'
                    join_response = session.post(
                        join_url,
                        headers=headers,
                        json={
                            "channel": channel.channel
                        }
                    )
                    url = "https://slack.com/api/conversations.members?channel=%s" % channel.channel
                    response = session.get(url, headers=headers)
                    data = response.json()
                    members = data.get('members', [])
                    slack_user_list = []
                    # Prefetch existing partners once per channel
                    existing_users = res_users.search([
                        ('slack_user_ref', 'in', members)
                    ])
                    partner_map = {p.slack_user_ref: p for p in existing_users}
                    for slack_user_ref in members:
                        user = partner_map.get(slack_user_ref)
                        if not user:
                            user_info_response = requests.get(
                                "https://slack.com/api/users.info",
                                headers=headers,
                                params={"user": slack_user_ref}
                            )
                            user_info_data = user_info_response.json()
                            user_info = user_info_data.get('user')
                            if user_info_data.get('ok') and user_info:
                                user = self.env['res.users'].create({
                                    'name': user_info.get('real_name'),
                                    'slack_user_ref': user_info.get('id'),
                                    'is_slack_internal_users': True,
                                    'login': user_info.get('profile') and user_info.get('profile').get(
                                        'email') or user_info.get('real_name') or '',
                                    'groups_id': [Command.set([self.env.ref('base.group_portal').id])],
                                    'company_ids': [Command.link(self.env.company.id)],
                                    'company_id': self.env.company.id
                                })
                                partner_map[slack_user_ref] = user
                        slack_user_list.append(user.partner_id.id)
                    # Existing channel members
                    channel_user_list = set(
                        channel.channel_member_ids.mapped('partner_id.id')
                    )
                    # Add only missing members
                    channel.channel_member_ids = [
                        Command.create({'partner_id': contact_id})
                        for contact_id in slack_user_list
                        if contact_id not in channel_user_list
                    ]
                except RequestException as e:
                    logger.error(f"Error occurred during API request: {str(e)}")
                except (KeyError, ValueError) as e:
                    logger.error(f"Error occurred while parsing API response: {str(e)}")
                except Exception as e:
                    logger.error(f"An error occurred: {str(e)}")
