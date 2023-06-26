# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from odoo import http
from odoo.http import request


class PosSystray(http.Controller):
    """
    The PosSystray Getting values to the pos chatter list, pos message and write
     the record to "mail.message".
    Methods:
        get_data_pos_systray(self):
           Getting data to the Message chatter list
        get_data_chat_box(self, **kw):
           kw contain the id of the channel and getting the message of the
           corresponding channel id.
        action_create_message_mail(self, **kw):
           creating new record in "mail.message"
    """

    @http.route('/pos_systray/message_data', auth='public', type='json')
    def get_data_pos_systray(self):
        """
        Summary:
            Getting data to the Message chatter list.
        Return:
            it contains details about chatter list.
        """
        return [{'id': mail_channel_id.id,
                 'type': mail_channel_id.channel_type,
                 'name': mail_channel_id.name,
                 'message_body': request.env['mail.message'].search(
                     [('model', '=', 'mail.channel'),
                      ('res_id', '=', mail_channel_id.id)], limit=1).body
                 } for mail_channel_id in request.env['mail.channel'].search([])
                for partner_id in mail_channel_id.channel_partner_ids
                if partner_id.id == request.env.user.partner_id.id]

    @http.route('/pos_systray/chat_message', auth='public', type='json')
    def get_data_chat_box(self, **kw):
        """
        Summary:
            getting the message of the corresponding channel id.
        Args:
            kw(dict):
                it contains channel id of the clicked channel.
        """
        return {
            'name': request.env['mail.channel'].browse(int(kw['data'])).name,
            'messages': [{
                'body': message_id.body,
                'author': message_id.author_id.name,
                'flag': 1 if message_id.author_id.id == request.env.user.
                partner_id.id else 0
            } for message_id in request.env['mail.message'].search(
                [('model', '=', 'mail.channel'),
                 ('res_id', '=', int(kw['data']))]).sorted('create_date')],
            'channel_id': int(kw['data'])
        }

    @http.route('/pos_chatter/send_message', auth='public', type='json')
    def action_create_message_mail(self, **kw):
        """
        Summary:
           creating new record in "mail.message"
        Args:
            kw(dict):
                it contains channel id of the clicked channel.
        """
        data = kw['data']
        request.env['mail.message'].sudo().create({
            'body': "<p>" + data['msg_body'] + "</p>",
            'model': 'mail.channel',
            'res_id': int(data['res_id']),
            'message_type': 'comment',
            'author_id': request.env.user.partner_id.id
        })
        return True
