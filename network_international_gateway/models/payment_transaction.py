# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.addons.payment import utils as payment_utils
from odoo.addons.network_international_gateway.controllers.payment_network_international import (
    NetworkInternational,
)

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Inherit the payment transactions, to add Network International specific functionality.
       Methods:
        _compute_reference: Override of `payment` to ensure that APS'
       requirements for references are satisfied.
       _get_specific_rendering_values: Override of _get_specific_rendering_values
       to handle specific rendering values for Network International.
       _get_tx_from_notification_data: Get payment status from Network International.
       _process_notification_data: Process the notification data received
       from Network International.
       """
    _inherit = 'payment.transaction'

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-',
                           **kwargs):
        """ Override of `payment` to ensure that APS' requirements for
        references are satisfied.

        APS' requirements for transaction are as follows: - References can
        only be made of alphanumeric characters and/or '-' and '_'. The
        prefix is generated with 'tx' as default. This prevents the prefix
        from being generated based on document names that may contain
        non-allowed characters (eg: INV/2020/...).

        :param str provider_code: The code of the provider handling the
        transaction.
        :param str prefix: The custom prefix used to compute the
        full reference.
        :param str separator: The custom separator used to separate the prefix
        from the suffix.
        :return: The unique reference
        for the transaction.
        :rtype: str
        """
        if provider_code == 'network_international':
            prefix = payment_utils.singularize_reference_prefix()
        return super()._compute_reference(provider_code, prefix=prefix,
                                          separator=separator, **kwargs)

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `_get_specific_rendering_values` to handle specific
        rendering values for Network International.

        :param processing_values: The processing values dictionary.
        :return: The rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'network_international':
            return res
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        sale_order = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids
        from_currency = self.company_id.currency_id
        _logger.info("Company Currency: %s", self.company_id.currency_id.name)
        _logger.info("Transaction Currency: %s", self.currency_id.name)
        to_currency = self.env['res.currency'].search([('name', '=', "AED")])
        order_amount_aed = from_currency._convert(
            self.amount - sale_order.amount_tax,
            to_currency,
            self.env.company.id,
            fields.Date.context_today(self)
        )
        api_endpoint = self.provider_id.api_endpoint
        outlet_reference = self.provider_id.outlet_reference
        auth_token = self.provider_id._get_authentication_token(
            f'{api_endpoint}/identity/auth/access-token')[
            'access_token']
        self.provider_id.auth_token = auth_token

        ni_values = {
            "action": "PURCHASE",
            "amount": {
                "currencyCode": "AED",
                "value": int(order_amount_aed * 100)
            },
            "merchantAttributes": {
                "skipConfirmationPage": False,
                "redirectUrl": urls.url_join(
                    base_url,
                    NetworkInternational._return_url
                )
            },
            "merchantOrderReference": processing_values.get('reference', '')
        }


        response_content = self.provider_id._network_international_make_request(
            url=f'{api_endpoint}/transactions/outlets/{outlet_reference}/orders',
            auth_token=auth_token,
            data=ni_values
        )
        _logger.info("NI Response: %s", response_content)
        payment_code = \
            str(response_content['_links'].get('payment', {}).get(
                'href')).split(
                'code=')[1]
        response_content['api_url'] = response_content['_links'].get('payment',
                                                                     {}).get(
            'href')
        if processing_values.get('reference') != '/':
            transaction = self.env['payment.transaction'].sudo().search(
                [('reference', '=', str(processing_values.get('reference')))],
                limit=1
            )
            transaction.sudo().write({
                'provider_reference': str(response_content['_id']),
            })

        return {
            'api_url': response_content['_links'].get('payment', {}).get(
                'href'),
            'code': payment_code
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Get payment status from Network International.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from Network International notification.
        :return: The transaction matching the reference.
        """
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'network_international':
            return tx


        merchant_ref = (
                notification_data.get('merchantOrderReference')
                or notification_data.get('_embedded', {})
                .get('payment', [{}])[0]
                .get('merchantOrderReference')
        )

        _logger.info("Merchant Reference: %s", merchant_ref)

        tx = self.search(
            [('reference', '=', merchant_ref)],
            limit=1
        )

        _logger.info("Found Transaction: %s", tx)

        return tx

    def _process_notification_data(self, notification_data):
        """
        Process the notification data received from Network International.

        This method processes the notification data and updates the payment
        state of the transaction accordingly.

        :param notification_data: The data received from Network International notification.
            """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'network_international':
            return
        payment_status = \
            notification_data.get("_embedded", {}).get("payment", [{}])[0].get(
                "state",
                "Unknown")
        if payment_status == "PURCHASED":
            self.sudo().write({'provider_reference': self.provider_reference})
            self._set_done()
            return True
        else:
            self.sudo().write(
                {'state_message': 'Network International: feedback error'})
            self._set_error(_("Your payment was refused."))
        return False