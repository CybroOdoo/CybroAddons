# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo import http, _
from odoo.http import request


class WebsitePaymentProof(http.Controller):
    """
    The WebsitePaymentProof updating the value of the sale order from the
    backend with the content that the customer
    uploaded in the frontend.
    Methods:
        payment_proof(self, **kw):
            onclick the save button creating new records in "ir.attachment" for
            the corresponding sale order working on
            "my account" screen.
        payment_screen_proof(self, **kw):
            onclick the save button creating new records in "ir.attachment" for
            the corresponding sale order working on "payment" screen.
        payment_show_receipt(self, **kw):
            onclick the show attachment button getting updated attachments.
    """

    @http.route(['/payment_proof/submit'], type='json', auth="public")
    def payment_proof(self, **kw):
        """
        Summary:
            onclick the save button creating new records in "ir.attachment" for
            the corresponding sale order working on
            "my account" screen.
        Args:
            kw(dict):
                it contains sale order id and contents of the input files.
        """
        if 'sale_id' in kw:
            sale_id = int(kw.get('sale_id'))
        else:
            sale_id = request.session.sale_order_id
        sale = request.env['sale.order'].sudo().browse(sale_id)
        for attachment in kw['attachments']:
            payment_proof_attachment = request.env[
                'ir.attachment'].sudo().create({
                'name': attachment['name'],
                'res_model': 'sale.order',
                'res_id': sale_id,
                'type': 'binary',
                'public': True,
                'datas': attachment['content'],
            })
            body = _("%s document is added by %s" % (
                attachment['name'], request.env.user.name))
            sale.message_post(body=body)
            copied_attachment = payment_proof_attachment.copy()

            mail_template = request.env.ref(
                'payment_proof_attachment'
                '.payment_proof_attachment_email_template').id
            template = request.env['mail.template'].browse(mail_template)
            template.attachment_ids = [(6, 0, [copied_attachment.id])]
            template.send_mail(sale_id, force_send=True)
            template.attachment_ids = [(3, copied_attachment.id)]
        return True

    @http.route(['/my_account_screen/show_updated'], type='json', auth="public")
    def payment_show_receipt(self, **kw):
        """
        Summary:
            onclick the show attachment button getting updated attachments.
        Args:
            kw(dict):
                it contains the id of the current sale order.
            Return(list):
                it contains the all attachments
        """
        if kw:
            sale_id = kw['data']
        else:
            sale_id = request.session.sale_order_id
        attachment_ids_list = []
        attachment_ids = request.env['ir.attachment'].sudo().search([(
            'res_model', '=', 'sale.order'), ('res_id', '=', sale_id),
            ('create_uid', '=', request.session.uid)])
        for attachment_id in attachment_ids:
            attachment_ids_list.append(({
                'id': attachment_id.id,
                'name': attachment_id.name
            }))
        return attachment_ids_list
