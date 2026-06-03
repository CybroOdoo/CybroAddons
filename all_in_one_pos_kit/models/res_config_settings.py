# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited Configuration Settings"""
    _inherit = "res.config.settings"

    enable_service_charge = fields.Boolean(
        string="Service Charges",
        config_parameter="all_in_one_pos_kit.enable_service_charge",
        help="Enable to add service charge")
    visibility = fields.Selection(
        [('global', 'Global'), ('session', 'Session')],
        default='global', string="Visibility",
        config_parameter="all_in_one_pos_kit.visibility",
        help='Setup the Service charge globally or per session')
    global_selection = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')],
        string='Type', default='amount',
        config_parameter="all_in_one_pos_kit.global_selection",
        help='Set the service charge as a amount or percentage')
    global_charge = fields.Float(
        string='Service Charge',
        config_parameter="all_in_one_pos_kit.global_charge",
        help='Set a default service charge globally')
    global_product_id = fields.Many2one(
        'product.product', string='Service Product',
        domain="[('available_in_pos', '=', True),('sale_ok', '=', True),"
               "('type', '=', 'service')]",
        config_parameter="all_in_one_pos_kit.global_product_id",
        help='Set a service product globally')
    custom_tip_percentage = fields.Float(
        string="Custom Percentage",
        config_parameter='all_in_one_pos_kit.custom_tip_percentage',
        help="enter the percentage custom tips")
    barcode = fields.Boolean(string='Order Barcode',
                             config_parameter='all_in_one_pos_kit.barcode',
                             help='Enable or disable the display of order '
                                  'barcode')
    invoice_number = fields.Boolean(
        string='Invoice Number',
        config_parameter='all_in_one_pos_kit.invoice_number',
        help='Enable or disable the display of invoice number')
    customer_details = fields.Boolean(
        string='Customer Details',
        config_parameter='all_in_one_pos_kit.customer_details',
        help='Enable or disable the display of customer details')
    customer_name = fields.Boolean(
        string='Customer Name',
        config_parameter='all_in_one_pos_kit.customer_name',
        help='Enable or disable the display of customer name')
    customer_address = fields.Boolean(
        string='Customer Address',
        config_parameter='all_in_one_pos_kit.customer_address',
        help='Enable or disable the display of customer address')
    customer_mobile = fields.Boolean(
        string='Customer Mobile',
        config_parameter='all_in_one_pos_kit.customer_mobile',
        help='Enable or disable the display of customer mobile number')
    customer_phone = fields.Boolean(
        string='Customer Phone',
        config_parameter='all_in_one_pos_kit.customer_phone',
        help='Enable or disable the display of customer phone number')
    customer_email = fields.Boolean(
        string='Customer Email',
        config_parameter='all_in_one_pos_kit.customer_email',
        help='Enable or disable the display of customer email')
    customer_vat = fields.Boolean(
        string='Customer VAT',
        config_parameter='all_in_one_pos_kit.customer_vat',
        help='Enable or disable the display of customer VAT number')
    customer_msg = fields.Boolean('POS Greetings',
                                  config_parameter='all_in_one_pos_kit.customer_msg',
                                  help='Create an account if you '
                                       'ever create an account')
    twilio_auth_token = fields.Char('Auth Token',
                             config_parameter='all_in_one_pos_kit.twilio_auth_token',
                             help='Copy the token from your twilio console '
                                  'window and paste here')
    account_sid = fields.Char('Account SID',
                              config_parameter='all_in_one_pos_kit.account_sid')
    twilio_number = fields.Char('Twilio Number',
                                config_parameter='all_in_one_pos_kit.twilio_number',
                                help='The number provided by '
                                     'twilio used to send '
                                     'text messages')
    sms_body = fields.Char('Body', config_parameter='all_in_one_pos_kit.sms_body')

    def set_values(self):
            """Override method to set configuration values.
                :return: Result of the super method"""
            res = super(ResConfigSettings, self).set_values()
            self.env['ir.config_parameter'].set_param(
                'pos.sms_body', self.sms_body)
            return res

    def get_values(self):
        """Override method to get configuration values.
           :return: Dictionary of configuration values"""
        res = super(ResConfigSettings, self).get_values()
        res.update(sms_body=self.env['ir.config_parameter'].sudo().get_param(
            'pos.sms_body'))
        return res
