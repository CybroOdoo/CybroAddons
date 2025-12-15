# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import Command, http
from odoo.http import request


class VapiAssistant(http.Controller):
    @http.route('/vapi_voice_assistant/details', type='json',
                auth='public', csrf=False, methods=['POST'])
    def final_details(self):
        """Processes final order details received from the voice assistant
         and creates a Sale Order in Odoo."""
        data = request.httprequest.get_json()
        call = data['message']['call']
        call_type = call.get('type')
        tool_call = data['message']['toolCalls'][0]
        arguments = tool_call['function']['arguments']
        details = arguments['OrderDetails']['Products']
        pr_list = []
        customer = ""
        for rec in details:
            pr_list.append(
                {"customer": rec['Customer'], "product": rec['Product'],
                 "id": rec['productId'], "qty": rec['Quantity'],
                 "variant": rec['Variant']})
            customer = rec['Customer']
        channel = "vapi_voice_channel"
        message = {"value": pr_list, "channel": channel}
        request.env["bus.bus"]._sendone(channel, "notification", message)
        if call_type == 'inboundPhoneCall':
            number = call['customer']['number']
            cust = request.env['res.partner'].sudo().search(
                [('phone', '=', number)])
            if not cust:
                cust = request.env['res.partner'].sudo().create({
                    'name': customer,
                    'phone': number,
                })
            sales = request.env['sale.order'].sudo().create({
                'partner_id': cust.id,
                'order_line': [
                    Command.create({
                        'product_id': recs['id'],
                        'product_uom_qty': recs["qty"],
                    }) for recs in pr_list]
            })
            sales.action_confirm()

    @http.route('/vapi_voice_assistant/status', type='json',
                auth='public', csrf=False, methods=['POST'])
    def get_status(self):
        """Receives status updates from the voice assistant"""
        data = request.httprequest.get_json()
        channel = "vapi_voice_channel"
        message = {"value": data, "channel": channel}
        request.env["bus.bus"]._sendone(channel, "notification", message)

    @http.route('/vapi_voice_assistant/language_details', type='json',
                auth='public', csrf=False, methods=['POST'])
    def get_language_details(self):
        """Returns language-specific configuration."""
        request.httprequest.get_json()
