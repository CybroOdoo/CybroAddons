# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
import uuid
import werkzeug

from odoo import http
from odoo.http import request


class PartnerConsolidatedPaymentLinkController(http.Controller):
    """
    Controller to handle request links for generating consolidated payments
    for outstanding dues of a partner.
    """

    @http.route(
        '/payment/balance/<int:partner_id>',
        type='http',
        auth='public',
        methods=['GET']
    )
    def create_payment_link(self, partner_id, access_token=None, **kwargs):
        """
        Generates or redirects to a payment link for the partner's total
        outstanding due amount and redirects the user to the Odoo payment page.
        """
        env = kwargs.get('env') or (request and request.env)
        if not env:
            raise werkzeug.exceptions.NotFound()

        partner = env['res.partner'].sudo().browse(partner_id)
        if not partner.exists():
            raise werkzeug.exceptions.NotFound()

        if not partner._check_consolidated_payment_token(access_token):
            raise werkzeug.exceptions.NotFound()

        company = partner.company_id or env.company
        overdue_amls_ids = partner.get_overdue_amls()
        if not overdue_amls_ids:
            return 'All outstanding invoices are settled.'

        currencies = overdue_amls_ids.mapped('currency_id')
        currency = overdue_amls_ids[0].currency_id
        total_due = partner.get_total_due(company)
        if currencies and len(currencies) > 1:
            currency = company.currency_id
            total_due = partner.get_total_due_in_company_currency()

        existing_refs = overdue_amls_ids.move_id.filtered(
            'consolidated_payment_link_ref'
        ).mapped('consolidated_payment_link_ref')
        reference = existing_refs[0] if existing_refs else str(uuid.uuid4())
        moves_to_update = overdue_amls_ids.move_id.filtered(
            lambda m: m.consolidated_payment_link_ref != reference
        )
        if moves_to_update:
            moves_to_update.write({'consolidated_payment_link_ref': reference})

        amount = currency.round(total_due)
        payment_token = partner.get_access_token(amount, currency.id)
        redirect_url = (
            f'/payment/pay?reference={reference}&amount={amount}'
            f'&currency_id={currency.id}&partner_id={partner.id}'
            f'&company_id={company.id}&access_token={payment_token}'
            f'&commercial_id={partner.id}&total_due={amount}'
        )
        if request:
            return request.redirect(redirect_url)
        return werkzeug.utils.redirect(redirect_url)
