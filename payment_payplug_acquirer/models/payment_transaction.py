# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
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
            self.env.company.id,
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
        api_url = self.env['payment.provider'].search(
            [('code', '=', 'payplug')]).payplug_end_point
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

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Get payment status from PayPlug.

        :param provider_code: The code of the provider handling the transaction.
        :param notification_data: The data received from PayPlug notification.
        :return: The transaction matching the reference.
        """
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    notification_data)
        if provider_code != 'payplug':
            return tx
        if isinstance(notification_data, object) == True:
            tx = self.search([('provider_reference', '=',
                               str(notification_data._attributes['id']))],
                             limit=1)
            if tx:
                vals = {
                    'reference': tx.reference.split('-')[0],
                    'customer_name': tx.partner_id.name,
                    'customer_postcode': tx.partner_id.zip,
                }
                key = notification_data.metadata.get('DigitalKey')
                control_digital_key = tx.provider_id._playplug_generate_digital_sign(
                    vals)
                if key.upper() != control_digital_key.upper():
                    raise ValidationError(
                        "PayPlug: " + _(
                            "Invalid Key: received %(sign)s, computed %(check)s",
                            sign=key.upper(), check=control_digital_key.upper()
                        )
                    )
            return tx

    def _process_notification_data(self, notification_data):
        """
        Process the notification data received from PayPlug.

        This method processes the notification data and updates the payment
        state of the transaction accordingly.

        :param notification_data: The data received from PayPlug notification.
            """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'payplug':
            return
        if notification_data.is_paid == True and notification_data.failure == None:
            self.sudo().write({'provider_reference': self.provider_reference})
            self._set_done()
            return True
        if notification_data.is_paid == False and notification_data.failure == None:
            self.sudo().write({'state_message': 'PayPlug: feedback error'})
            self._set_pending()
            return None
        if notification_data.is_paid == False and notification_data.failure != None:
            self.sudo().write({'state_message': 'PayPlug: feedback error'})
            self._set_error(_("Your payment was refused."))
        return False
