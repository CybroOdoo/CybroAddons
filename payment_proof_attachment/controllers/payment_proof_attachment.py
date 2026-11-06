# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
import binascii
import logging

from odoo import Command, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

_logger = logging.getLogger(__name__)

# Marker stored on the attachments created by this module, so that only the
# payment proofs (and not the internal documents of the order) are listed.
PAYMENT_PROOF_DESCRIPTION = 'payment_proof_attachment'


class WebsitePaymentProof(CustomerPortal):
    """
    Lets the customer upload payment proofs for a sale order from the
    website and list the proofs already uploaded.
    """

    def _get_sale_order(self, **kw):
        """
        Return the sale order the current visitor is allowed to access.

        The order is taken from the ``sale_id`` (or ``data``) parameter and
        checked with the portal access rules / ``access_token``. When no
        valid id is given, the current website cart is used.

        Returns:
            sale.order: sudoed sale order, or an empty recordset
        """
        sale_order = request.env['sale.order']
        sale_id = kw.get('sale_id') or kw.get('data')
        if sale_id:
            try:
                return self._document_check_access(
                    'sale.order', int(sale_id), kw.get('access_token'))
            except (ValueError, TypeError):
                _logger.warning("Invalid sale order id received: %s", sale_id)
            except (AccessError, MissingError):
                return sale_order
        return request.cart or sale_order

    @http.route(['/payment_proof/submit'], type='jsonrpc', auth="public",
                website=True)
    def payment_proof(self, **kw):
        """
        Summary:
            onclick the save button creating new records in "ir.attachment"
            for the corresponding sale order

        Args:
            kw(dict): it contains sale order id, access token and contents
                      of the input files.

        Returns:
            dict: success or error message
        """
        sale = self._get_sale_order(**kw)
        if not sale:
            return {'error': request.env._('Sale order not found')}

        attachments = request.env['ir.attachment'].sudo()
        for attachment in kw.get('attachments') or []:
            name = attachment.get('name') or 'payment_proof'
            content = attachment.get('content') or ''
            if ',' in content:
                # strip the "data:<mimetype>;base64," prefix of data URLs
                content = content.split(',', 1)[1]
            try:
                raw = base64.b64decode(content.strip(), validate=True)
            except (binascii.Error, ValueError):
                _logger.warning("Invalid content for payment proof %s", name)
                continue
            attachments |= attachments.create({
                'name': name,
                'res_model': 'sale.order',
                'res_id': sale.id,
                'type': 'binary',
                'description': PAYMENT_PROOF_DESCRIPTION,
                'raw': raw,
            })

        if not attachments:
            return {'error': request.env._('No valid attachment received')}

        sale.message_post(
            body=request.env._(
                "%(names)s uploaded as payment proof by %(user)s",
                names=", ".join(attachments.mapped('name')),
                user=request.env.user.name,
            ),
            attachment_ids=attachments.ids,
        )
        mail_template = request.env.ref(
            'payment_proof_attachment.payment_proof_attachment_email_template',
            raise_if_not_found=False)
        if mail_template:
            mail_template.sudo().send_mail(
                sale.id,
                force_send=True,
                email_values={
                    'attachment_ids': [
                        Command.link(att.id) for att in attachments],
                },
            )
        return {
            'success': True,
            'message': request.env._('Attachments uploaded successfully'),
        }

    @http.route(['/my_account_screen/show_updated'], type='jsonrpc',
                auth="public", website=True)
    def payment_show_receipt(self, **kw):
        """
        Summary:
            onclick the show attachment button getting updated attachments.

        Args:
            kw(dict): it contains the id and access token of the current
                      sale order.

        Return:
            list: the payment proofs of the order with their download url
        """
        sale = self._get_sale_order(**kw)
        if not sale:
            return {'error': request.env._('Sale order not found')}

        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', sale.id),
            ('description', '=', PAYMENT_PROOF_DESCRIPTION),
        ])
        tokens = attachments.generate_access_token()
        return [{
            'id': attachment.id,
            'name': attachment.name,
            'url': '/web/content/%s?download=true&access_token=%s' % (
                attachment.id, token),
        } for attachment, token in zip(attachments, tokens)]
