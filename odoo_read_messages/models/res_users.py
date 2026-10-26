#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import _, models
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    """Inheriting the res users model to read all messages"""
    _inherit = 'res.users'

    def action_read_messages(self):
        """Read all messages and notifications for the selected user(s)"""
        if not (self.env.is_admin() or self <= self.env.user):
            raise AccessError(_("You are only allowed to mark your own messages as read."))

        partners = self.mapped('partner_id')
        if not partners:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

        # Mark unread mail notifications as read for target user(s) (recipient)
        unread_notifications = self.env['mail.notification'].sudo().search([
            ('res_partner_id', 'in', partners.ids),
            ('is_read', '=', False),
        ])
        if unread_notifications:
            unread_notifications.write({'is_read': True})

        # Cancel failure/bounce/exception notifications for messages authored by target user(s)
        failed_notifications = self.env['mail.notification'].sudo().search([
            ('author_id', 'in', partners.ids),
            ('notification_status', 'in', ['bounce', 'exception']),
        ])
        if failed_notifications:
            failed_notifications.write({'notification_status': 'canceled'})

        # Mark discuss channel messages as read for target user(s)
        channel_members = self.env['discuss.channel.member'].sudo().search([
            ('partner_id', 'in', partners.ids)
        ])
        channel_ids = channel_members.channel_id.ids
        if channel_ids:
            latest_messages = dict(self.env['mail.message']._read_group(
                [('model', '=', 'discuss.channel'), ('res_id', 'in', channel_ids)],
                groupby=['res_id'],
                aggregates=['id:max'],
            ))
            for member in channel_members:
                latest_message_id = latest_messages.get(member.channel_id.id)
                if latest_message_id:
                    member._mark_as_read(latest_message_id)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
