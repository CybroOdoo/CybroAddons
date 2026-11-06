# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from urllib.parse import urlencode

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class PaymentController(http.Controller):
    """Controller to generate consolidated payment links for partner outstanding balances."""

    @http.route('/payment/balance/<int:partner_id>', type='http', auth='public', methods=['GET'])
    def create_payment_link(self, partner_id, access_token=None, **kwargs):
        """Create and redirect to a consolidated payment link for the partner's overdue balance.

        :param partner_id: ID of the partner whose balance is paid
        :param access_token: Token generated for the partner's payment link
        :param kwargs: other query parameters
        :return: HTTP redirection or status message string
        """
        partner = request.env['res.partner'].sudo().browse(partner_id).exists()
        if not partner or not partner._check_consolidated_payment_token(access_token):
            raise NotFound()
        values = partner._prepare_consolidated_payment_values()
        if not values:
            return request.make_response(
                request.env._("All outstanding invoices are settled."))
        currency = values['currency']
        company = values['company']
        query = urlencode({
            'reference': values['reference'],
            'amount': values['amount'],
            'currency_id': currency.id,
            'partner_id': partner.id,
            'company_id': company.id,
            'access_token': partner.get_access_token(values['amount'], currency.id),
        })
        return request.redirect(f'/payment/pay?{query}')
