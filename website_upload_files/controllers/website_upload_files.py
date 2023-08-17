# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleFileUpload(WebsiteSale):
    """For attaching the file in website sale order"""

    @http.route('/shop/payment', type='http', auth='public', website=True,
                sitemap=False)
    def shop_payment(self, **post):
        """ Payment step. This page proposes several payment means based on
        available payment.provider. State at this point :
        - a draft sales
        order with lines; otherwise, clean context / session and back to the
        shop
        - no transaction in context / session, or only a draft one,
        if the customer did go to a payment provider website but closed the
        tab without paying / canceling
        """
        order = request.website.sale_get_order()
        redirection = self.checkout_redirection(
            order) or self.checkout_check_address(order)
        if redirection:
            return redirection
        render_values = self._get_shop_payment_values(order, **post)
        render_values['only_services'] = order and order.only_services or False
        if render_values['errors']:
            render_values.pop('providers', '')
            render_values.pop('tokens', '')
        if post.get('attachment'):
            if post.get('attachment', False):
                file = post.get('attachment')
                request.env['ir.attachment'].sudo().create({
                    'name': post.get('attachment').filename,
                    'res_name': post.get('attachment').filename,
                    'type': 'binary',
                    'res_model': 'sale.order',
                    'res_id': order.id,
                    'datas': base64.b64encode(file.read()),
                })
        all_attachments = request.env['ir.attachment'].search(
            [('res_model', '=', 'sale.order'), ('res_id', '=', order.id)])
        render_values['attachment'] = all_attachments
        return request.render("website_sale.payment", render_values)

    @http.route('/shop/attachments', type='json', auth='public', website=True,
                sitemap=False)
    def shop_attachments(self, **post):
        """For delete the attachment from websites"""
        attachment = request.env['ir.attachment'].sudo().browse(int(post.get(
            "attachment_id")))
        attachment.unlink()
        return
