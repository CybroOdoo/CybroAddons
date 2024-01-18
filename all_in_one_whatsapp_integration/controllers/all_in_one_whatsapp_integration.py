# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import Command, http
from odoo.http import request


class Webhook(http.Controller):
    """ Cloud api webhook controller """

    @http.route('/whatsapp_message', type='http', auth='public',
                methods=['GET', 'POST'],
                csrf=False)
    def get_webhook_url(self, **kwargs, ):
        """ function create portal user and send message to live chat"""
        if kwargs:
            return (kwargs['hub.challenge'])
        else:
            active_user = request.env['res.users'].browse(request.uid)
            data = request.get_json_data()
            number = data['entry'][0]['changes'][0]['value']
            if number['contacts']:
                profile = number['contacts'][0]
            channel_partner_ids = []
            channel_partner_ids.append(active_user.partner_id.id)
            to_partner = request.env['res.partner'].sudo().search([
                ('phone', '=', str(number['metadata']['display_phone_number']))
            ])
            if to_partner:
                channel_partner_ids.append(to_partner.id)
            contact = request.env['res.partner'].sudo().search([
                ('name', '=', profile['profile']['name']),
                ('phone', '=', profile['wa_id'])
            ])
            if contact:
                channel_partner_ids.append(contact.id)
            else:
                contact = request.env['res.users'].sudo().create({
                    'name': profile['profile']['name'],
                    'company_id': active_user.company_id.id,
                    'login': profile['profile']['name'],
                    'groups_id': [
                        Command.set(
                            [request.env.ref('base.group_portal').id])],
                }).partner_id
                contact.phone = profile['wa_id']
                channel_partner_ids.append(contact.id)
            message_content = \
                data['entry'][0]['changes'][0]['value']['messages'][0]
            channel = request.env['mail.channel'].sudo().search([
                ('phone', '=', profile['wa_id']),
                ('channel_partner_ids', 'in', channel_partner_ids)
            ])
            if not channel:
                channel = request.env['mail.channel'].sudo().create({
                    'channel_partner_ids': [(4, contact.id),
                                            (4, to_partner.id)],
                    'channel_type': 'livechat',
                    'name': profile['profile']['name'],
                    'phone': profile['wa_id'],
                    'livechat_operator_id': "3"
                })
            uuid = channel.uuid
            mail_channel = request.env["mail.channel"].sudo().search(
                [('uuid', '=', uuid)], limit=1)
            body = message_content['text']['body']
            x = mail_channel.with_context(
                mail_create_nosubscribe=True).message_post(
                author_id=contact.id,
                body=body,
                message_type='comment',
                subtype_xmlid='mail.mt_comment'
            )
