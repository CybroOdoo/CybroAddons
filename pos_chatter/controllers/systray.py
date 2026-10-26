# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arshad Ali Pottengal (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request
from odoo.tools import plaintext2html


class SystrayController(http.Controller):
    """
    The PosSystray Getting values to the pos chatter list, pos message and
    posting messages to discuss channels.
    """

    @http.route('/pos_systray/message_data', auth='user', type='jsonrpc')
    def get_data_pos_systray(self):
        partner_id = request.env.user.partner_id.id
        channels = request.env['discuss.channel'].search([
            ('channel_partner_ids', 'in', [partner_id])
        ])

        members = request.env['discuss.channel.member'].search([
            ('channel_id', 'in', channels.ids),
            ('partner_id', '=', partner_id),
        ])
        unread_by_channel = {m.channel_id.id: m.message_unread_counter for m in members}

        data = []
        for mail_channel in channels:
            message = request.env['mail.message'].search(
                [('model', '=', 'discuss.channel'),
                 ('res_id', '=', mail_channel.id)],
                limit=1, order="id desc"
            )
            data.append({
                'message_id': message.id if message else False,
                'id': mail_channel.id,
                'type': mail_channel.channel_type,
                'name': mail_channel.name,
                'message_body': message.body if message else "",
                'count': unread_by_channel.get(mail_channel.id, 0),
            })
        return data

    @http.route('/pos_systray/chat_message', auth='user', type='jsonrpc')
    def get_data_chat_box(self, **kw):
        """
        Summary:
            getting the message of the corresponding channel id.
        """
        raw_id = kw.get('data')
        if not raw_id:
            return {'name': '', 'messages': [], 'channel_id': False}
        try:
            channel_id = int(raw_id)
        except (ValueError, TypeError):
            return {'name': '', 'messages': [], 'channel_id': False}

        partner_id = request.env.user.partner_id.id
        channel = request.env['discuss.channel'].search([
            ('id', '=', channel_id),
            ('channel_partner_ids', 'in', [partner_id]),
        ], limit=1)
        if not channel:
            return {'name': '', 'messages': [], 'channel_id': channel_id}

        messages = request.env['mail.message'].search([
            ('model', '=', 'discuss.channel'),
            ('res_id', '=', channel_id)
        ], order="id asc")

        # Mark messages in this channel as read for the current user
        member = request.env['discuss.channel.member'].search([
            ('channel_id', '=', channel.id),
            ('partner_id', '=', partner_id),
        ], limit=1)
        if messages and member:
            member._mark_as_read(messages[-1].id)

        return {
            'name': channel.name or "",
            'messages': [{
                'body': message_id.body or "",
                'author': message_id.author_id.name or "",
                'flag': 1 if message_id.author_id.id == partner_id else 0
            } for message_id in messages],
            'channel_id': channel_id
        }

    @http.route('/pos_chatter/send_message', auth='user', type='jsonrpc')
    def action_create_message_mail(self, **kw):
        """
        Summary:
           Post new message in discuss channel.
        Args:
            kw(dict):
                it contains channel id of the clicked channel.
        """
        data = kw.get('data', {})
        res_id = data.get('res_id')
        msg_body = (data.get('msg_body') or '').strip()
        if not res_id or not msg_body:
            return False

        try:
            channel_id = int(res_id)
        except (ValueError, TypeError):
            return False

        partner_id = request.env.user.partner_id.id
        channel = request.env['discuss.channel'].search([
            ('id', '=', channel_id),
            ('channel_partner_ids', 'in', [partner_id]),
        ], limit=1)
        if not channel:
            return False

        channel.message_post(
            body=plaintext2html(msg_body)   ,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        return True
