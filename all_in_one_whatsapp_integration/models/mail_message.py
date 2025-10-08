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
import http.client
import json
from odoo import api, models


class MailMessage(models.Model):
    """This class extends the base 'mail.message' model in Odoo to include
        functionality for sending WhatsApp messages using Facebook Graph API.
       """
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, values_list):
        """This method creates a new mail message and then sends the message's
        body as a WhatsApp message using the Facebook Graph API."""
        bearer_token = self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_whatsapp_integration.bearer_token')
        whatsapp_no = self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_whatsapp_integration.whatsapp_no')
        if bearer_token and whatsapp_no and values_list[0]['model'] == 'mail.channel':
            if values_list[0]['email_from']:
                mail_channel = self.env['mail.channel'].browse(
                    values_list[0]['res_id'])
                if mail_channel:
                    conn = http.client.HTTPSConnection("graph.facebook.com")
                    payload = json.dumps({
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": mail_channel.phone,
                        "type": 'text',
                        "text": {
                            "preview_url": False,
                            "body": values_list[0]['body']
                        }
                    })
                    headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {bearer_token}'
                    }
                    conn.request("POST", f"/v17.0/{whatsapp_no}/messages",
                                 payload,
                                 headers)
                    response = conn.getresponse()
        return super(MailMessage, self).create(values_list)
