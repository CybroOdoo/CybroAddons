# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import logging

from odoo import http
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.website_sale.controllers.main import WebsiteSale
_logger = logging.getLogger(__name__)


class WebsiteSalePayment(WebsiteSale):
    @http.route('/shop/payment/validate', type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_validate(self, transaction_id=None, sale_order_id=None,
                              **post):
        """ Method that should be called by the server when receiving an update
        for a transaction. State at this point :

         - UDPATE ME
        """
        if sale_order_id is None:
            order = request.website.sale_get_order()
        else:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            assert order.id == request.session.get('sale_last_order_id')

        if transaction_id:
            tx = request.env['payment.transaction'].sudo().browse(
                transaction_id)
            assert tx in order.transaction_ids()
        elif order:
            tx = order.get_portal_last_transaction()
        else:
            tx = None

        if not order or (order.amount_total and not tx):
            return request.redirect('/shop')

        if order and not order.amount_total and not tx:
            order.with_context(send_email=True).action_confirm()
            return request.redirect(order.get_portal_url())
        website_order_configuration = request.env[
            'ir.config_parameter'].sudo().get_param(
                'website_sale_auto_backend.website_order_configuration')
        if website_order_configuration == 'confirm_order':
            if order.state in ('draft', 'sent'):
                order.with_context(send_email=True).action_confirm()
        elif website_order_configuration == 'confirm_order_create_inv':
            if order.state in ('draft', 'sent'):
                order.with_context(send_email=True).action_confirm()
            order._force_lines_to_invoice_policy_order()
            invoices = order._create_invoices()
            # Setup access token in advance to avoid serialization failure between
            # edi postprocessing of invoice and displaying the sale order on the portal
            for invoice in invoices:
                invoice._portal_ensure_token()
            tx.invoice_ids = [(6, 0, invoices.ids)]
        elif website_order_configuration == 'confirm_order_post_inv':
            if order.state in ('draft', 'sent'):
                order.with_context(send_email=True).action_confirm()
            order._force_lines_to_invoice_policy_order()
            invoices = order._create_invoices()
            # Setup access token in advance to avoid serialization failure between
            # edi postprocessing of invoice and displaying the sale order on the portal
            for invoice in invoices:
                invoice._portal_ensure_token()
                invoice.action_post()
            tx.invoice_ids = [(6, 0, invoices.ids)]
        elif website_order_configuration == 'confirm_quotation_create_payment':
            if order.state in ('draft', 'sent'):
                order.with_context(send_email=True).action_confirm()
            order._force_lines_to_invoice_policy_order()
            invoices = order._create_invoices()
            # Setup access token in advance to avoid serialization failure between
            # edi postprocessing of invoice and displaying the sale order on the portal
            for invoice in invoices:
                invoice._portal_ensure_token()
                invoice.action_post()
            tx.invoice_ids = [(6, 0, invoices.ids)]
            tx._set_done()
            if tx.acquirer_id.provider != 'transfer':
                tx._create_payment()
            else:
                request.env['account.payment.register'].with_context(
                    active_ids=tx.invoice_ids.ids,
                    active_model='account.move').create({
                        'payment_date': tx.last_state_change,
                    })._create_payments()
        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            return request.redirect('/shop')

        PaymentPostProcessing.remove_transactions(tx)
        return request.redirect('/shop/confirmation')
