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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited Configuration Settings"""
    _inherit = "res.config.settings"

    # pos.config fields
    pos_is_service_charges = fields.Boolean(
        related='pos_config_id.is_service_charges', readonly=False,
    string="Service Charges", help="Enable Service Charges")
    pos_visibility_type = fields.Selection(
        related='pos_config_id.visibility_type',
        readonly=False, help="Can choose visibility of service charges.")
    pos_service_charge = fields.Float(related='pos_config_id.service_charge',
                                      readonly=False, help="Charge need to apply")
    pos_service_product_id = fields.Many2one(
        'product.product',
        compute='_compute_pos_service_product_id', store=True, readonly=False,
        domain="[('type', '=', 'service')]")
    pos_service_charge_type = fields.Selection(
        related='pos_config_id.service_charge_type',
        readonly=False)

    @api.depends('company_id', 'pos_is_service_charges', 'pos_config_id')
    def _compute_pos_service_product_id(self):
        """Compute service product based on the company and other fields"""
        default_product = self.env.ref(
            "point_of_sale.product_product_consumable",
            raise_if_not_found=False) or self.env['product.product']
        for res_config in self:
            service_product = res_config.pos_config_id.service_product_id or (
                default_product)
            if (res_config.pos_is_service_charges) and (
                    not service_product.company_id or (
                    service_product.company_id) == res_config.company_id):
                res_config.pos_service_product_id = service_product
            else:
                res_config.pos_service_product_id = False


    custom_tip_percentage = fields.Float(
        string="Custom Percentage",
        config_parameter='all_in_one_pos_kit.custom_tip_percentage',
        help="enter the percentage custom tips")
    barcode = fields.Boolean(
        related='pos_config_id.show_order_barcode', readonly=False,
        string='Order Barcode',
        help='Enable or disable the display of order barcode on the receipt')
    invoice_number = fields.Boolean(
        related='pos_config_id.show_invoice_number', readonly=False,
        string='Invoice Number',
        help='Enable or disable the display of invoice number on the receipt')
    customer_details = fields.Boolean(
        related='pos_config_id.customer_details',
        string="Customer Details",
        help="By Enabling the customer details"
             " in pos receipt",
        readonly=False
    )
    customer_name = fields.Boolean(
        related='pos_config_id.customer_name',
        string="Customer Name",
        help="By Enabling the customer name "
             "in pos receipt",
        readonly=False
    )
    customer_address = fields.Boolean(
        related='pos_config_id.customer_address',
        string="Customer Address",
        help="By Enabling the customer Address "
             "in pos receipt",
        readonly=False
    )
    customer_mobile = fields.Boolean(
        related='pos_config_id.customer_mobile',
        string="Customer Mobile",
        help="By Enabling the customer mobile "
             "in pos receipt",
        readonly=False
    )
    customer_phone = fields.Boolean(
        related='pos_config_id.customer_phone',
        string="Customer Phone",
        help="By Enabling the customer phone "
             "in pos receipt",
        readonly=False
    )
    customer_email = fields.Boolean(
        related='pos_config_id.customer_email',
        string="Customer Email",
        help="By Enabling the customer email "
             "in pos receipt",
        readonly=False
    )
    customer_vat = fields.Boolean(
        related='pos_config_id.customer_vat',
        string="Customer VAT",
        help="By Enabling the customer vat details "
             "in pos receipt",
        readonly=False
    )

    customer_msg = fields.Boolean('POS Greetings',
                                  config_parameter='all_in_one_pos_kit.customer_msg',
                                  help='Send a greeting SMS through Twilio to the '
                                       'customer when a POS order is paid')
    twilio_auth_token = fields.Char('Auth Token',
                             config_parameter='all_in_one_pos_kit.twilio_auth_token',
                             help='Copy the token from your twilio console '
                                  'window and paste here')
    account_sid = fields.Char('Twilio Account SID',
                              config_parameter='all_in_one_pos_kit.account_sid')
    twilio_number = fields.Char(
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
        # The service product is a computed (not related) field, so it has
        # to be written to the POS configuration explicitly, otherwise the
        # selected product is lost on save.
        for rec in self:
            if rec.pos_config_id and rec.pos_is_service_charges:
                rec.pos_config_id.service_product_id = (
                    rec.pos_service_product_id)
        return res

    def get_values(self):
        """Override method to get configuration values.
           :return: Dictionary of configuration values"""
        res = super(ResConfigSettings, self).get_values()
        res.update(sms_body=self.env['ir.config_parameter'].sudo().get_param(
            'pos.sms_body'))
        return res
