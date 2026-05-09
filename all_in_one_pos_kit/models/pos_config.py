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


class PosConfig(models.Model):
    """Inherited POS Configuration to add field's and functions"""
    _inherit = 'pos.config'

    is_session = fields.Boolean(string="Session",
                                compute='_compute_is_session',
                                help="Check it is for sessions")
    is_service_charges = fields.Boolean(string="Service Charges",
                                        help="Enable to add service charge")
    charge_type = fields.Selection([('amount', 'Amount'),
                                    ('percentage', 'Percentage')],
                                   string='Type', default='amount',
                                   help="Can choose charge percentage or "
                                        "amount")
    service_charge = fields.Float(string='Service Charge',
                                  help="Charge need to apply")
    service_product_id = fields.Many2one(
        'product.product', string='Service Product',
        domain="[('available_in_pos', '=', True),('sale_ok', '=', True),"
               "('type', '=', 'service')]", help="Service Product")
    # Global service charge fields (computed from config parameters)
    enable_service_charge = fields.Boolean(
        string="Enable Service Charge",
        compute='_compute_global_service_charge',
        help="Global enable service charge flag")
    sc_visibility = fields.Char(
        string="Service Charge Visibility",
        compute='_compute_global_service_charge',
        help="Global or session visibility")
    global_selection = fields.Char(
        string="Global Selection",
        compute='_compute_global_service_charge',
        help="Global charge type: amount or percentage")
    global_charge = fields.Float(
        string="Global Charge",
        compute='_compute_global_service_charge',
        help="Global service charge amount")
    global_product_id = fields.Integer(
        string="Global Product ID",
        compute='_compute_global_service_charge',
        help="Global service product ID")
    image = fields.Binary(string='Image', help='Add logo for pos session')
    user_ids = fields.Many2many('res.users', 'pos_config_res_users_rel',
                                'pos_config_id', 'res_users_id',
                                string='Allowed Users',
                                help="The users who are allowed to access this"
                                     "POS.")
    is_allowed_pos = fields.Boolean(compute='_compute_is_allowed_pos',
                                   search='_search_is_allowed_pos')
    customer_details = fields.Boolean(string=" Customer Details",
                                      help="By Enabling the customer details"
                                           " in pos receipt")
    customer_name = fields.Boolean(string=" Customer Name",
                                   help="By Enabling the customer name "
                                        "in pos receipt")
    customer_address = fields.Boolean(string=" Customer Address",
                                      help="By Enabling the customer Address "
                                           "in pos receipt")
    customer_mobile = fields.Boolean(string=" Customer Mobile",
                                     help="By Enabling the customer mobile "
                                          "in pos receipt")
    customer_phone = fields.Boolean(string=" Customer Phone",
                                    help="By Enabling the customer phone "
                                         "in pos receipt")
    customer_email = fields.Boolean(string=" Customer Email",
                                    help="By Enabling the customer email "
                                         "in pos receipt")
    customer_vat = fields.Boolean(string=" Customer Vat",
                                  help="By Enabling the customer vat details "
                                       "in pos receipt")

    def _compute_global_service_charge(self):
        """Compute global service charge settings from config parameters"""
        ICP = self.env['ir.config_parameter'].sudo()
        enable = ICP.get_param(
            'all_in_one_pos_kit.enable_service_charge', 'False')
        visibility = ICP.get_param(
            'all_in_one_pos_kit.visibility', 'global')
        selection = ICP.get_param(
            'all_in_one_pos_kit.global_selection', 'amount')
        charge = ICP.get_param(
            'all_in_one_pos_kit.global_charge', '0')
        product_id = ICP.get_param(
            'all_in_one_pos_kit.global_product_id', '0')
        for rec in self:
            rec.enable_service_charge = enable == 'True'
            rec.sc_visibility = visibility or 'global'
            rec.global_selection = selection or 'amount'
            try:
                rec.global_charge = float(charge)
            except (ValueError, TypeError):
                rec.global_charge = 0.0
            try:
                rec.global_product_id = int(product_id)
            except (ValueError, TypeError):
                rec.global_product_id = 0

    def _compute_is_session(self):
        """To check the service charge is set up for session wise or
        globally"""
        is_session = self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_pos_kit.visibility') == 'session'
        for rec in self:
            rec.is_session = is_session

    def _load_pos_data(self, data):
        """Override to inject computed service charge fields into POS data"""
        result = super()._load_pos_data(data)
        config = self.env['pos.config'].browse(
            result['data'][0]['id'])
        # Add computed fields that aren't stored
        result['data'][0]['enable_service_charge'] = config.enable_service_charge
        result['data'][0]['sc_visibility'] = config.sc_visibility
        result['data'][0]['global_selection'] = config.global_selection
        result['data'][0]['global_charge'] = config.global_charge
        result['data'][0]['global_product_id'] = config.global_product_id
        return result

    @api.onchange('is_service_charges')
    def _onchange_is_service_charges(self):
        """When the service charge is enabled set service product
        and amount by default per session"""
        if self.is_service_charges:
            if not self.service_product_id:
                self.service_product_id = self.env['product.product'].search(
                    [('available_in_pos', '=', True), ('sale_ok', '=', True),
                     ('type', '=', 'service')], limit=1)
                self.service_charge = 10.0
        else:
            self.service_product_id = False
            self.service_charge = 0.0

    def _compute_is_allowed_pos(self):
        """Computed field to check if the current user is allowed to access
        this POS"""
        allowed_configs = self.env.user.pos_config_ids
        for record in self:
            record.is_allowed_pos = not allowed_configs or record.id in allowed_configs.ids

    def _search_is_allowed_pos(self, operator, value):
        """Search function for is_allowed_pos to filter dashboard properly"""
        allowed_configs = self.env.user.pos_config_ids
        if allowed_configs:
            # If user has some shops assigned, restrict strictly to those
            return [('id', 'in', allowed_configs.ids)]
        # If no assignments at all, show everything (default behavior)
        return []
