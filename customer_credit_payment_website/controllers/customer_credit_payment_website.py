# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request


class CreditDetails(http.Controller):
    """ Controllers to get the credit details and the credit amount of each
    partner."""

    @http.route('/credit/details', type='http', auth='public', website=True,
                csrf=False)
    def credit_details(self, **post):
        """ Get the credit amount for each user and return the credit payment
        page."""
        credit_amount = request.env.user.credit_amount
        return request.render(
            'customer_credit_payment_website.credit_payment_page',
            {'credit_amount': credit_amount})

    @http.route('/add/credit/balance', type='http', auth='public', website=True,
                csrf=False)
    def add_credit_balance(self, **post):
        """ Add the credit amount from the website."""
        return request.render(
            'customer_credit_payment_website.add_credit_payment_page')


class PaymentCreditPayController(http.Controller):
    _simulation_url = '/payment/credit_pay/simulate_payment'

    @http.route('/payment/credit_pay/simulate_payment', type='json',
                auth='public')
    def credit_pay_simulate_payment(self, **data):
        """ Simulate the response of a payment request.

        :param dict data: The simulated notification data.
        :return: None
        """
        return request.env[
            'payment.transaction'].sudo()._handle_notification_data(
            'credit_pay', data.get('args'))
