# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import _, api, models
from odoo.addons.payment_paytabs_odoo.controllers.payment_paytabs_odoo import PaymentPaytabs
from odoo.exceptions import ValidationError, _logger
from werkzeug import urls


class PaymentTransaction(models.Model):
    """This class represents a payment transaction that can be used to pay."""
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """Returns a list of rendering values for api connections """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'paytabs':
            return res
        api_url = 'https://secure-global.paytabs.com/payment/request'
        domain_url = self.env['payment.acquirer'].search([('provider', '=', 'paytabs')]).domain
        paytabs_values = {
            "profile_id": int(self.acquirer_id.profile_id),
            "tran_type": "sale",
            "tran_class": "ecom",
            "cart_description": self.reference,
            "cart_id": self.reference,
            "cart_currency": self.currency_id.name,
            "cart_amount": processing_values['amount'],
            'return': urls.url_join(domain_url,
                                    PaymentPaytabs._return_url),
            'callback': urls.url_join(domain_url,
                                      PaymentPaytabs._return_url),

            "api_url": api_url,
            "customer_details": {
                "name": self.partner_name,
                "email": self.partner_email,
                "street1": self.partner_address,
                "city": self.partner_city,
                "state": self.partner_state_id.name,
                "country": self.partner_country_id.name,
                "ip": "127.0.0.1"
            },
        }
        response_content = self.acquirer_id._paytabs_make_request(api_url,
                                                                  paytabs_values)
        response_content['api_url'] = response_content.get('redirect_url')
        return response_content

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """Returns the tx from feedback data """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != 'paytabs':
            return tx

        reference = data.get('cartId')
        tx = self.search(
            [('reference', '=', reference), ('provider', '=', 'paytabs')])
        if not tx:
            raise ValidationError(
                "Paytabs: " + _("No transaction found matching reference %s.",
                                reference)
            )
        return tx

    def _process_feedback_data(self, data):
        """It checks the feedback data that is authorised, Error or approved"""
        super()._process_feedback_data(data)
        if self.provider != 'paytabs':
            return

        self.acquirer_reference = data.get('cartId')
        status = data.get('respStatus')
        if status == 'A':
            self._set_done(state_message="Authorised")
        elif status == 'APPROVED':
            self._set_pending(
                state_message="Authorised but on hold for further anti-fraud review")
        elif status in ('E', 'D'):
            self._set_canceled(state_message="Error")
        else:
            _logger.warning(
                "received unrecognized payment state %s for transaction with reference %s",
                status, self.reference
            )
            self._set_error("PayTabs: " + _("Invalid payment status."))
