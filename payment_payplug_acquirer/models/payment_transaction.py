# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.http import request
from werkzeug import urls
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_payplug_acquirer.controllers.payment_payplug_acquirer import PaymentPayPlug

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Inherit the payment transactions, to add PayPlug specific functionality.
       Methods:
           _compute_reference: Override of `payment` to ensure that APS'
       requirements for references are satisfied.
       _get_specific_rendering_values: Override of
       `_get_specific_rendering_values` to handle specific rendering values
       for PayPlug.
       _get_tx_from_notification_data: Get payment status from PayPlug.
       _process_notification_data: Process the notification data received
       from PayPlug.
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
        if provider_code == 'payplug':
            prefix = payment_utils.singularize_reference_prefix()
        return super()._compute_reference(provider_code, prefix=prefix,
                                          separator=separator, **kwargs)

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `_get_specific_rendering_values` to handle specific
        rendering values for PayPlug.

        :param processing_values: The processing values dictionary.
        :return: The rendering values."""
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'payplug':
            return res

        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        sale_order = self.env['payment.transaction'].search(
            [('id', '=', self.id)]).sale_order_ids
        from_currency = self.company_id.currency_id
        to_currency = self.env['res.currency'].search([('name', '=', "EUR")])
        order_amount_eur = from_currency._convert(
            self.amount - sale_order.amount_tax,
            to_currency,
            self.env.company,
            fields.Date.context_today(self)
        )
        payment_generate_key = {
            'reference': processing_values['reference'].split('-')[0],
            'customer_name': sale_order.partner_id.name,
            'customer_postcode': sale_order.partner_id.zip,
        }
        digital_key = self.env[
            'payment.provider']._playplug_generate_digital_sign(
            payment_generate_key)
        payplug_values = {
            "amount": int(order_amount_eur * 100),
            "currency": 'EUR',
            "save_card": False,
            "customer": {
                "first_name": self.partner_name,
                "last_name": self.partner_name,
                "address1": self.partner_address,
                "address2": self.partner_address,
                "city": self.partner_city,
                "country": self.partner_country_id.code,
                "email": self.partner_email,
                "postcode": self.partner_country_id.code
            },
            "hosted_payment": {
                "return_url": urls.url_join(base_url,
                                            PaymentPayPlug._return_url) + '?transaction=' + str(
                    self.id),
            },
            "metadata": {
                "customer_id": self.partner_id.id,
                'DigitalKey': digital_key,
            },
        }
        # A transaction is already tied to the exact provider configuration
        # chosen at checkout.  Looking up providers by code can return more
        # than one record (for example, across companies), which makes the
        # field access fail with an Expected singleton error.
        api_url = self.provider_id.payplug_end_point
        response_content = self.provider_id._payplug_make_request(
            api_url, payplug_values)
        response_content['api_url'] = response_content.get('hosted_payment',
                                                           {}).get(
            'payment_url')

        if processing_values.get('reference') != '/':
            transaction_id = request.env['payment.transaction'].sudo().search(
                [('reference', '=', str(processing_values.get('reference')))],
                limit=1)
            transaction_id.sudo().write({
                'provider_reference': str(response_content['id'])})

        return response_content

    @api.model
    def _search_by_reference(self, provider_code, payment_data):
        """Find a PayPlug transaction from the payment identifier.

        Odoo 19 processes provider feedback through ``_process`` instead of
        the removed ``_get_tx_from_notification_data`` API.
        """
        if provider_code != 'payplug':
            return super()._search_by_reference(provider_code, payment_data)

        provider_reference = getattr(payment_data, 'id', None)
        if not provider_reference:
            provider_reference = getattr(payment_data, '_attributes', {}).get('id')
        return self.search([
            ('provider_reference', '=', str(provider_reference)),
            ('provider_code', '=', 'payplug'),
        ], limit=1)

    def _extract_amount_data(self, payment_data):
        """Skip amount validation for PayPlug SDK payment objects."""
        if self.provider_code != 'payplug':
            return super()._extract_amount_data(payment_data)
        return None

    def _apply_updates(self, payment_data):
        """Apply the state returned by PayPlug using Odoo 19's API."""
        if self.provider_code != 'payplug':
            return super()._apply_updates(payment_data)

        received_key = getattr(payment_data, 'metadata', {}).get('DigitalKey')
        if received_key:
            values = {
                'reference': self.reference.split('-')[0],
                'customer_name': self.partner_id.name,
                'customer_postcode': self.partner_id.zip,
            }
            expected_key = self.provider_id._playplug_generate_digital_sign(values)
            if received_key.upper() != expected_key.upper():
                raise ValidationError(
                    _(
                        "PayPlug: Invalid Key: received %(sign)s, computed %(check)s",
                        sign=received_key.upper(), check=expected_key.upper(),
                    )
                )

        provider_reference = getattr(payment_data, 'id', None)
        if not provider_reference:
            provider_reference = getattr(payment_data, '_attributes', {}).get('id')
        if provider_reference:
            self.provider_reference = str(provider_reference)

        if payment_data.is_paid and not payment_data.failure:
            self._set_done()
        elif payment_data.failure:
            self._set_error(_("Your payment was refused."))
        else:
            self._set_pending()
