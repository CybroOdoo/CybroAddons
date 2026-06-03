# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (contact@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
from odoo import models


class ResUsers(models.Model):
    """ Inheriting the res users model to read all messages"""
    _inherit = 'res.users'

    def action_read_messages(self):
        """Read all Messages"""
        # Cancel exception notifications for current partner only
        exception_notifications = self.env['mail.notification'].sudo().search([
            ('notification_status', '=', 'exception'),
            ('res_partner_id', '=', self.env.user.partner_id.id),
        ])
        exception_notifications.write({'notification_status': 'canceled'})

        # Mark all needaction notifications (Inbox) as read
        self.env['mail.message'].mark_all_as_read()

        # Mark unread channel/chat messages as read
        channel_members = self.env['discuss.channel.member'].search([
            ('partner_id', '=', self.env.user.partner_id.id)
        ])
        for member in channel_members:
            latest_message = self.env['mail.message'].search([
                ('model', '=', 'discuss.channel'),
                ('res_id', '=', member.channel_id.id),
                ('message_type', 'not in', ['notification', 'user_notification']),
                ('id', '>', member.seen_message_id.id or 0)
            ], limit=1, order='id desc')
            if latest_message:
                member.channel_id._set_last_seen_message(latest_message)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }