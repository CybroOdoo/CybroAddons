# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Viswanth K(odoo@cybrosys.com)
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
#############################################################################
import logging
import werkzeug
from odoo import http
from odoo.http import request
from odoo.addons.payment import utils as payment_utils
import uuid

_logger = logging.getLogger(__name__)


class PaymentController(http.Controller):
    """Controller to generate consolidated payment links for partner outstanding balances."""

    @http.route('/payment/balance/<int:partner_id>', type='http', auth='public', methods=['GET'], website=True, csrf=False, cors='*')
    def create_payment_link(self, *args, **post):
        """Create and redirect to a consolidated payment link for the partner's overdue balance.

        :param args: positional arguments
        :param post: query parameters including partner_id
        :return: HTTP redirection or status message string
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
            total_due = partner.get_total_due(company)
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
