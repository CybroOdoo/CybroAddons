# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
###############################################################################
import base64

import requests

from odoo import fields, models


class PosOrder(models.Model):
    """Inherit the pos_order model to implement the functionality of sending
    invoices and receipts by calling the UltraMsg API."""
    _inherit = 'pos.order'

    def action_send_invoice(self, **kwargs):
        """Sends an invoice to the customer via WhatsApp using
        the UltraMsg API."""
        instant = self.env['configuration.manager'].search(
            [('state', '=', 'verified'),
             ('config_id', '=', kwargs.get('config_id'))], limit=1)
        order = self.search([('id', '=', kwargs.get('order_id'))])
        if not order.account_move:
            order.action_pos_order_invoice()
        attachment_id = self.env['ir.attachment'].search([
            ('res_model', '=', 'mail.message'),
            ('res_id', 'in', order.account_move.message_ids.ids)])
        if not attachment_id:
            report = self.env['ir.actions.report']._render_qweb_pdf(
                "account.account_invoices", order.account_move.ids[0])
            values = {
                'name': "Invoice" + order.name,
                'type': 'binary',
                'datas': base64.b64encode(report[0]),
                'store_fname': base64.b64encode(report[0]),
                'mimetype': 'application/pdf',
            }
            attachment_id = self.env['ir.attachment'].create(values)
        if instant:
            if order.partner_id.whatsapp_number:
                url = f"https://api.ultramsg.com/{instant.instance}/messages/document"
                payload = {
                    "token": instant.token,
                    "to": order.partner_id.whatsapp_number,
                    "filename": attachment_id.name,
                    "document": attachment_id.datas.decode('utf-8'),
                    "caption": "Your Invoice is here",
                }
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                try:
                    response = requests.post(url, data=payload, headers=headers)
                    response.raise_for_status()
                    if response.status_code == 200:
                        self.env['whatsapp.message'].create({
                            'status': 'sent',
                            'from_user_id': self.env.user.id,
                            'to_user': order.partner_id.whatsapp_number,
                            'user_name': order.partner_id.name,
                            'body': 'Your Invoice is here',
                            'attachment_id': attachment_id.id,
                            'date_and_time_sent': fields.datetime.now()
                        })
                except requests.RequestException as e:
                    return {'status': 'error', 'message': str(e)}
            else:
                return {'status': 'error',
                        'message': 'Partner have not a Whatsapp Number'}
        else:
            return {'status': 'error',
                    'message': 'You are not connected with API'}

    def action_send_receipt(self, name, partner, ticket):
        """ Sends a receipt on WhatsApp if WhatsApp is enabled and
        the partner has a WhatsApp number is provided."""
        self.ensure_one()
        filename = 'Receipt-' + name + '.jpg'
        receipt = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': ticket,
            'res_model': 'pos.order',
            'res_id': self.ids[0],
            'mimetype': 'image/jpeg',
        })
        instant = self.env['configuration.manager'].search(
            [('state', '=', 'verified'),
             ('config_id', '=', partner['config_id'])], limit=1)
        if instant:
            if partner['whatsapp']:
                url = f"https://api.ultramsg.com/{instant.instance}/messages/document"
                payload = {
                    "token": instant.token,
                    "to": partner['whatsapp'],
                    "filename": receipt.name,
                    "document": receipt.datas.decode('utf-8'),
                    "caption": "Your Receipt is here",
                }
                headers = {'content-type': 'application/x-www-form-urlencoded'}
                try:
                    response = requests.post(url, data=payload, headers=headers)
                    response.raise_for_status()
                    if response.status_code == 200:
                        self.env['whatsapp.message'].create({
                            'status': 'sent',
                            'from_user_id': self.env.user.id,
                            'to_user': partner['whatsapp'],
                            'user_name': partner['name'],
                            'body': 'Your Receipt is here',
                            'attachment_id': receipt.id,
                            'date_and_time_sent': fields.datetime.now()
                        })
                except requests.RequestException as e:
                    return {'status': 'error', 'message': str(e)}
            else:
                return {'status': 'error',
                        'message': 'Partner have not a Whatsapp Number'}
        else:
            return {'status': 'error',
                    'message': 'You are not connected with API'}

    def get_instance(self, **kwargs):
        """Retrieves the verified configuration instance."""
        instant = self.env['configuration.manager'].search(
            [('state', '=', 'verified'),
             ('config_id', '=', kwargs.get('config_id'))], limit=1)
        return {
            'instant_id': instant.id
        }
