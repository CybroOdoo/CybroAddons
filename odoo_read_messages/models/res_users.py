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
from odoo import fields, models


class ResUsers(models.Model):
    """ Inheriting the res users model to read all messages"""
    _inherit = 'res.users'

    def action_read_messages(self):
        """Read all Messages"""
        # Cancel exception notifications
        exception_notifications = self.env['mail.notification'].sudo().search([
            ('notification_status', '=', 'exception'),
        ])
        exception_notifications.write({'notification_status': 'canceled'})
        # Mark unread notifications as read
        # Reading the messages from the channels.
        channel_members = self.env['discuss.channel.member'].search([
            ('partner_id', '=', self.env.user.partner_id.id)
        ])
        # Fetch the latest message
        latest_message = self.env['mail.message'].search([
            ('model', '=', 'mail.channel'),
            ('message_type', 'not in', ['notification', 'user_notification']),
            (
                'id', '>',
                max(channel_members.mapped('seen_message_id.id') or [0]))
        ], limit=1, order='id desc')
        if latest_message:
            channel_members.write({
                'seen_message_id': latest_message.id,
                'fetched_message_id': latest_message.id,
                'last_seen_dt': fields.Datetime.now(),
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
