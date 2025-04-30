# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
from odoo import api, fields, models


class PosConfig(models.Model):
    """Inherited POS Configuration to add field's and functions"""
    _inherit = 'pos.config'
    is_qr_code = fields.Boolean(string='Order QRCode',
                                help='Enable this field to show the '
                                     'qr code to pos receipt')
    is_invoice_number = fields.Boolean(string='Invoice Number',
                                       help='Enable this field to show the '
                                            'invoice number to pos receipt')
    is_customer_details = fields.Boolean(string='Customer Details',
                                         help='Enable this field to show the '
                                              'customer number to pos receipt')
    is_customer_name = fields.Boolean(string='Customer Name',
                                      help='Enable this field to show '
                                           'the customer name to pos receipt')
    is_customer_address = fields.Boolean(string='Customer Address',
                                         help='Enable this field to show '
                                              'the customer address code to '
                                              'pos receipt')
    is_customer_mobile = fields.Boolean(string='Customer Mobile',
                                        help='Enable this field to show the '
                                             'customer mobile to pos receipt')
    is_customer_phone = fields.Boolean(string='Customer Phone',
                                       help='Enable this field to show the '
                                            'customer phone to pos receipt')
    is_customer_email = fields.Boolean(string='Customer Email',
                                       help='Enable this field to show the '
                                            'customer email to pos receipt')
    is_customer_vat = fields.Boolean(string='Customer VAT',
                                     help='Enable this field to show the '
                                          'customer vat to pos receipt')
    custom_tip_percentage = fields.Float(string="Custom Percentage",
                                         help="Enter the percentage custom tips"
                                              "you want to apply")
    image = fields.Binary(string='Image', help='Add logo for pos session')
    is_session = fields.Boolean(string="Session",
                                compute='_compute_check_session',
                                help="Check it is for sessions", )
    is_service_charges = fields.Boolean(string="Service Charges",
                                        help="Enable to add service charge")
    charge_type = fields.Selection(
        [('amount', 'Amount'),
         ('percentage', 'Percentage')],
        string='Type', default='amount',
        help="Can choose charge percentage or amount")
    service_charge = fields.Float(string='Service Charge',
                                  help="Charge need to apply")
    service_product_id = fields.Many2one('product.product',
                                         string='Service Product',
                                         domain="[('available_in_pos', '=', "
                                                "True),"
                                                "('sale_ok', '=', True), "
                                                "('type', '=', 'service')]",
                                         help="Service Product")
    enable_service_charge = fields.Boolean(
        string="Service Charges",
        help="Enable to add service charge")
    visibility = fields.Selection(
        [('global', 'Global'), ('session', 'Session')],
        default='global', string="Visibility",
        help='Setup the Service charge globally or per session')
    global_selection = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')],
        string='Type', default='amount',
        help='Set the service charge as a amount or percentage')
    global_charge = fields.Float(
        string='Service Charge',
        help='Set a default service charge globally')
    global_product_id = fields.Many2one(
        'product.product', string='Service Product',
        domain="[('available_in_pos', '=', True),('sale_ok', '=', True),"
               "('type', '=', 'service')]",
        help='Set a service product globally')
    customer_msg = fields.Boolean('POS Greetings',
                                  Help='Create an account if you ever create '
                                       'an account')
    auth_token = fields.Char('Auth Token',
                             Help='Copy the token from your twilio console '
                                  'window adn paste here')
    account_sid = fields.Char('Account SID')
    twilio_number = fields.Char('Twilio Number',
                                Help='The number provided by twilio used to '
                                     'send text messages')
    sms_body = fields.Text('Body')

    def _compute_check_session(self):
        """To check the service charge is set up for session wise or globally"""
        check_session = self.env['ir.config_parameter'].sudo().get_param(
            'service_charges_pos.visibility')
        if check_session == 'session':
            self.is_session = True
        else:
            self.is_session = False

    @api.onchange('is_service_charges')
    def onchange_is_service_charges(self):
        """When the service charge is enable set service product
        and amount by default per session"""
        if self.is_service_charges:
            if not self.service_product_id:
                domain = [('available_in_pos', '=', True),
                          ('sale_ok', '=', True), ('type', '=', 'service')]
                self.service_product_id = self.env[
                    'product.product'].search(
                    domain, limit=1)
                self.service_charge = 10.0
        else:
            self.service_product_id = False
            self.service_charge = 0.0
