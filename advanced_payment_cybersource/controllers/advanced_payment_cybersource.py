"""Cybersource payment"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<odoo@cybrosys.com>)
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
import json
import os
from CyberSource import *
from CyberSource.logging.log_configuration import LogConfiguration
from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


class WebsiteSaleFormCyberSource(http.Controller):
    """This class is used to do the payment"""

    @http.route('/payment/cybersource/simulate_payment', type='json',
                auth='public')
    def payment_with_flex_token(self, **post):
        """This is used to Payment processing using the flex token"""
        address = request.env['res.partner'].browse(
            post.get('values')['partner'])
        client_reference_information = Ptsv2paymentsClientReferenceInformation(
            code=post.get('reference'))
        processing_information_capture = False
        if post:
            processing_information_capture = True
        processing_information = Ptsv2paymentsProcessingInformation(
            capture=processing_information_capture,
            commerce_indicator="vbv")
        payment_information_tokenized_card = Ptsv2paymentsPaymentInformationTokenizedCard(
            number=post.get('customer_input')[
                'card_num'],
            expiration_month=post.get('customer_input')['exp_month'],
            expiration_year=post.get('customer_input')['exp_year'],
            transaction_type="1")
        payment_information = Ptsv2paymentsPaymentInformation(
            tokenized_card=payment_information_tokenized_card.__dict__)
        order_information_amount_details = Ptsv2paymentsOrderInformationAmountDetails(
            total_amount=post.get('values')[
                'amount'],
            currency=request.env[
                'res.currency'].browse(post.get('values')['currency']).name)
        order_information_bill_to = Ptsv2paymentsOrderInformationBillTo(
            first_name=address.name.split(' ')[
                           0] or address.name,
            last_name=address.name.split(' ')[
                          1] or address.name,
            address1=address.state_id.name or False,
            locality=address.city or False,
            administrative_area="CA",
            postal_code=address.zip or False,
            country=address.country_id.name or False,
            email=address.email,
            phone_number=address.phone)
        order_information = Ptsv2paymentsOrderInformation(
            amount_details=order_information_amount_details.__dict__,
            bill_to=order_information_bill_to.__dict__)
        consumer_authentication_information = Ptsv2paymentsConsumerAuthenticationInformation(
            cavv="AAABCSIIAAAAAAACcwgAEMCoNh+=",
            xid="T1Y0OVcxMVJJdkI0WFlBcXptUzE=")
        request_obj = CreatePaymentRequest(
            client_reference_information=client_reference_information.__dict__,
            processing_information=processing_information.__dict__,
            payment_information=payment_information.__dict__,
            order_information=order_information.__dict__,
            consumer_authentication_information=consumer_authentication_information.__dict__)
        request_obj = self.del_none(request_obj.__dict__)
        request_obj = json.dumps(request_obj)
        try:
            client_config = self.get_configuration()
            api_instance = PaymentsApi(client_config)
            return_data, status, body = api_instance.create_payment(request_obj)
            status_data = {'reference': post.get('reference'),
                           'payment_details': post.get('customer_input')[
                               'card_num'], 'simulated_state': 'done'}
            if status == 201:
                request.env[
                    'payment.transaction'].sudo()._handle_notification_data(
                    'cybersource', status_data)
            else:
                raise ValidationError(_("Your Payment has not been processed"))
            return return_data
        except Exception as e:
            _logger.info(
                "\nException when calling PaymentsApi->create_payment: %s\n" % e)

    if __name__ == "__main__":
        """This is used to Payment processing using the flex token"""
        payment_with_flex_token()

    def get_configuration(self):
        """This is used to Payment provider configuration"""
        record = request.env['payment.provider'].sudo().search(
            [('code', '=', 'cybersource')])
        configuration_dictionary = {
            "authentication_type": "http_signature",
            "merchantid": record.cyber_merchant,
            "run_environment": "apitest.cybersource.com",
            "request_json_path": "",
            "key_alias": "testrest",
            "key_password": "testrest",
            "key_file_name": "testrest",
            "keys_directory": os.path.join(os.getcwd(), "resources"),
            "merchant_keyid": record.cyber_key,
            "merchant_secretkey": record.cyber_secret_key,
            "use_metakey": False,
            "portfolio_id": "",
            "timeout": 1000,
        }
        log_config = LogConfiguration()
        log_config.set_enable_log(True)
        log_config.set_log_directory(os.path.join(os.getcwd(), "Logs"))
        log_config.set_log_file_name("cybs")
        log_config.set_log_maximum_size(10487560)
        log_config.set_log_level("Debug")
        log_config.set_enable_masking(False)
        log_config.set_log_format(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        log_config.set_log_date_format("%Y-%m-%d %H:%M:%S")
        configuration_dictionary["log_config"] = log_config
        return configuration_dictionary

    def del_none(self, data):
        """This is used to checks any value having null"""
        for key, value in list(data.items()):
            if value is None:
                del data[key]
            elif isinstance(value, dict):
                self.del_none(value)
        return data
