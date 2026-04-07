# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class WebsitePaymentProof(http.Controller):
    """
    The WebsitePaymentProof updating the value of the sale order from the
    backend with the content that the customer uploaded in the frontend.
    """

    def _get_sale_order_id(self, **kw):
        """
        Helper method to get sale_order_id from various sources

        Returns:
            int: sale_order_id or None
        """
        sale_id = None
        if 'sale_id' in kw:
            sale_id = int(kw.get('sale_id'))
        elif 'data' in kw:
            sale_id = int(kw.get('data'))

        if not sale_id:
            sale_id = request.session.get('sale_order_id')
        if not sale_id:
            order = request.website.sale_get_order()
            if order:
                sale_id = order.id

        return sale_id

    @http.route(['/payment_proof/submit'], type='jsonrpc', auth="public")
    def payment_proof(self, **kw):
        """
        Summary:
            onclick the save button creating new records in "ir.attachment"
            for the corresponding sale order

        Args:
            kw(dict): it contains sale order id and contents of the input files.

        Returns:
            dict: success or error message
        """
        sale_id = self._get_sale_order_id(**kw)
        if not sale_id:
            return {'error': 'No sale order found'}
        sale = request.env['sale.order'].sudo().browse(sale_id)
        if not sale.exists():
            return {'error': 'Sale order not found'}

        attached_files = kw.get('attachments', [])

        for attachment in attached_files:
            name = attachment['name']
            content = attachment['content']

            payment_proof_attachment = request.env[
                'ir.attachment'].sudo().create({
                'name': name,
                'res_model': 'sale.order',
                'res_id': sale_id,
                'type': 'binary',
                'public': True,
                'datas': content,
            })

            copied_attachment = payment_proof_attachment.copy()
            body = "%s document is added by %s" % (
                attachment['name'],
                request.env.user.name
            )
            sale.message_post(body=body)

            try:
                mail_template = request.env.ref(
                    'payment_proof_attachment.payment_proof_attachment_email_template'
                )

                if mail_template:
                    mail_template.attachment_ids = [
                        (6, 0, [copied_attachment.id])
                    ]
                    mail_template.send_mail(sale_id, force_send=True)
                    mail_template.attachment_ids = [(3, copied_attachment.id)]
            except Exception as e:
                _logger.error("Error sending email: %s", str(e))

        return {'success': True, 'message': 'Attachments uploaded successfully'}

    @http.route(['/my_account_screen/show_updated'], type='jsonrpc', auth="public")
    def payment_show_receipt(self, **kw):
        """
        Summary:
            onclick the show attachment button getting updated attachments.

        Args:
            kw(dict): it contains the id of the current sale order.

        Return:
            list: it contains all attachments
        """
        sale_id = self._get_sale_order_id(**kw)

        if not sale_id:
            return {'error': 'No sale order found'}

        user_id = request.env.user.id
        attachment_ids_list = []

        attachment_ids = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', int(sale_id)),
            ('create_uid', '=', user_id)
        ])

        for attachment_id in attachment_ids:
            attachment_ids_list.append({
                'id': attachment_id.id,
                'name': attachment_id.name,
                'url': '/web/content/%s' % attachment_id.id
            })
        return attachment_ids_list
