# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

import logging
import uuid

import werkzeug

from odoo import http
from odoo.http import request

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PartnerConsolidatedPaymentLinkController(http.Controller):
    """
    Controller to handle request links for generating consolidated payments
    for outstanding dues of a partner.
    """

    @http.route('/payment/balance/<int:partner_id>', type='http', auth='public', methods=['GET'], website=True, csrf=False, cors='*')
    def create_payment_link(self, *args, **post):
        """
        Generates a payment link for the partner's total outstanding due amount
        and redirects the user to the Odoo payment page.
        """
        partner_id = post.get('partner_id')
        if not partner_id:
            raise werkzeug.exceptions.NotFound()
        partner = request.env['res.partner'].sudo().browse(partner_id)
        company = partner.company_id or request.env.user.company_id
        overdue_amls_ids = partner.get_overdue_amls()
        if overdue_amls_ids:
            currencies = overdue_amls_ids.mapped('currency_id')
            currency = overdue_amls_ids[0].currency_id
            total_due = partner.get_consolidated_total_due(company)
            if currencies and len(currencies) > 1:
                currency = company.currency_id
                total_due = partner.get_total_due_in_company_currency()
            reference = str(uuid.uuid4())
            overdue_amls_ids.move_id.write({'consolidated_payment_link_ref': reference})
            amount = currency.round(total_due)
            access_token = partner.get_access_token(amount, currency.id)
            redirect_url = f'/payment/pay?reference={reference}&amount={amount}&currency_id={currency.id}&partner_id={partner_id}&company_id={company.id}&access_token={access_token}&commercial_id={partner_id}&total_due={amount}'
            return request.redirect(redirect_url)
        else:
            return 'All outstanding invoices are settled.'
