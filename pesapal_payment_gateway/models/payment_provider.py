# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author: Arjun S(odoo@cybrosys.com)
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
from odoo import fields, models


class PaymentProvider(models.Model):
    """ Inherited class of payment provider to add pesapal functions"""
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('pesapal', "Pesapal")],
        ondelete={'pesapal': 'set default'}
    )
    pesapal_consumer_key = fields.Char(string="Consumer Key",
                                       help="Pesapal consumer key")
    pesapal_consumer_secret = fields.Char(string="Consumer Secret",
                                          help="Pesapal consumer secret")
    token_request_url = fields.Char(
        "Token URL", help="The URL of the Token url",
        default='https://cybqa.pesapal.com/pesapalv3/api/Auth/RequestToken',
        config_parameter="pesapal_payment_gateway.token_request_url")
    token_register_url = fields.Char(
        "Token Register URL", help="The URL for the registration",
        default='https://cybqa.pesapal.com/pesapalv3/api/URLSetup/RegisterIPN',
        config_parameter="pesapal_payment_gateway.token_register_url")
    payment_submit_url = fields.Char(
        "Token Register URL", help="URL for the submit the payment order",
        default='https://cybqa.pesapal.com/pesapalv3/api/Transactions/SubmitOrderRequest',
        config_parameter="pesapal_payment_gateway.payment_submit_url")
    payment_status_url = fields.Char(
        " URL", help="URL for to get the status of the payment order",
        default='https://cybqa.pesapal.com/pesapalv3/api/Transactions/GetTransactionStatus?orderTrackingId=',
        config_parameter="pesapal_payment_gateway.payment_status_url")
