"""Home delivery payment"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class PaymentProcess(WebsiteSale):
    """This is used to process the payment """
    @http.route('/shop/payment', type='http', auth='public', website=True,
                sitemap=False)
    def shop_payment(self, **post):
        """ Payment step. This page proposes several payment means based on available
                payment.provider"""
        if post.get('order_id'):
            order = request.env['sale.order'].sudo().browse(post.get('order_id'))
            order.write({
                'website_id': request.website.id
            })
            request.session['sale_order_id'] = post.get('order_id')
            if order:
                order._force_lines_to_invoice_policy_order()
                invoices = order._create_invoices()
                report = request.env['ir.actions.report']._render_qweb_pdf(
                    "account.account_invoices",
                    invoices.id)
                data_record = base64.b64encode(report[0])
                ir_values = {
                    'name': 'Invoice Report',
                    'type': 'binary',
                    'datas': data_record,
                    'store_fname': data_record,
                    'mimetype': 'application/pdf',
                    'res_model': 'account.move',
                }
                report_attachment = request.env['ir.attachment'].sudo().create(
                    ir_values)
                email_template = request.env.ref(
                    'home_delivery_system.email_template_invoiced')
                if email_template:
                    email_template.attachment_ids = [(4, report_attachment.id)]
                    email_template.send_mail(order.id,
                                             force_send=True)
                    email_template.attachment_ids = [(5, 0, 0)]
        else:
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
        request.session['sale_last_order_id'] = order.id
        return request.render("website_sale.payment", render_values)
