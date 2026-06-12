# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
import html2text
import imghdr
import os
import requests
from pdf2image import convert_from_bytes
from odoo import fields, models


class AccountMove(models.Model):
    """This class extends 'account.move' and adds custom fields and methods
       for sending WhatsApp messages with attachments."""
    _inherit = 'account.move'

    whatsapp_message = fields.Text(string="WhatsApp Message",
                                   help="Enter the message to be sent via "
                                        "WhatsApp.")
    attachment_ids = fields.Many2many('ir.attachment',
                                      'whatsapp_attachment_rel',
                                      'email_template_id',
                                      'attachment_id',
                                      string='Attachments',
                                      help="Attachments to include in the"
                                           " WhatsApp message.")
    message_type = fields.Selection(string='Message Type',
                                    selection=[('text', 'Text'),
                                               ('image', 'Image'),
                                               ('pdf', 'Pdf')],
                                    help='Select the type of message '
                                         '(Text, Image, or Pdf).')
    image_files = fields.Image(string='Image File',
                               help='Upload an image file.')

    def action_send_message(self, pos_reference, option_name):
        """Send a custom WhatsApp message with attachments and text messages.
        Args:
        pos_reference (str): The point of sale reference.
        option_name (str): The message type option ('text', 'image', or 'pdf').
        Returns:
            dict: Response JSON from the WhatsApp API."""
        pos_order = self.env['pos.order'].search(
            [('pos_reference', '=', pos_reference)])
        var = 'body'
        template_id = self.env.ref(
            "pos_invoice_in_whatsapp.pos_order_whatsapp_template").id
        mail_template_values = (
            self.env["mail.template"]
            .with_context(tpl_partners_only=True)
            .browse(template_id)
            .generate_email([pos_order.id], fields=["body_html"]))
        body_html = dict(mail_template_values).get(pos_order.id, {}).pop(
            "body_html",
            "")
        account_move_id = self.search([('ref', '=', pos_order.name)])
        account_move_id.write({'message_type': option_name})
        report_attachment = self.env['ir.attachment'].search(
            [('res_id', '=', account_move_id.id)], order='create_date desc',
            limit=1)
        report = report_attachment.name
        file_path = report_attachment._full_path(report_attachment.store_fname)
        files = {
            "file": (
                report, open(file_path, "rb"), report_attachment.mimetype,
                {'filename': report}),
        }
        report_attachment.public = True
        bearer_token = self.env['ir.config_parameter'].sudo().get_param(
            'pos_invoice_in_whatsapp.auth_token')
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": pos_order.partner_id.mobile,
            "type": account_move_id.message_type,
            "preview_url": False,
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {bearer_token}'
        }
        if account_move_id.message_type == 'text':
            payload["text"] = {var: html2text.html2text(body_html)}
        elif account_move_id.message_type == 'pdf':
            token = {'Authorization': f'Bearer {bearer_token}'}
            url = "https://graph.facebook.com/v17.0/110521242060381/media"
            response = requests.post(url, data=payload, files=files,
                                     headers=token)
            data = response.json()
            doc = data.get('id')
            payload['type'] = 'document'
            payload["document"] = {
                'id': doc,
                'filename': report_attachment.name
            }
        else:
            if report_attachment:
                pdf_data = base64.b64decode(report_attachment.datas)
                images = convert_from_bytes(pdf_data)
                output_folder = f'/tmp/temp.{type(report_attachment)}'
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                for i, image in enumerate(images):
                    image_path = os.path.join(output_folder,
                                              f'page_{i + 1}.png')
                    image.save(image_path)
                    image_type = imghdr.what(image_path)
                    with open(image_path, 'rb') as image_file:
                        image_data = base64.b64encode(image_file.read())
                    attachment_record = self.env['ir.attachment'].create({
                        'name': os.path.basename(image_path),
                        'mimetype': f'image/{image_type}',
                        'datas': image_data,
                        'res_model': 'account.move',
                    })
                    if attachment_record:
                        files = {
                            "file": (
                                report,
                                open(
                                    attachment_record._full_path(
                                        attachment_record.store_fname
                                    ), "rb"
                                ),
                                attachment_record.mimetype,
                                {},
                            ),
                        }
                        token = {
                            'Authorization': f'Bearer {bearer_token}'
                        }
                        url = "https://graph.facebook.com/v17.0/110521242060381/media"
                        response = requests.post(url, data=payload,
                                                 files=files, headers=token)
                        data = response.json()
                        image = data.get('id')
                        payload['type'] = 'image'
                        payload['image'] = {
                            'id': image,
                        }
        response = requests.post(
            f"https://graph.facebook.com/v17.0/110521242060381/messages",
            json=payload, headers=headers
        )
        response.json()
        return response.status_code
