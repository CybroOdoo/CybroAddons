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
from odoo.exceptions import UserError



class PosConfig(models.Model):
    """Inherited POS Configuration to add field's and functions"""
    _inherit = 'pos.config'

    is_session = fields.Boolean(string="Session",
                                compute='_compute_is_session',
                                help="Check it is for sessions")
    is_service_charges = fields.Boolean("Service Charges", help="Enable Service Charges")
    visibility_type = fields.Selection([
        ('global', 'Global'),
        ('session', 'Session')],
        string='Visibility', default='global',
        help="Can choose visibility of service charges.")
    service_charge = fields.Float(
                                  help="Charge need to apply",
                                  default=10.0)
    service_product_id = fields.Many2one('product.product',
                                         domain="[('sale_ok', '=', True)]",
                                         help="Service Product")
    service_charge_type = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')],
        string='Type', default='amount',
        help="Can choose charge percentage or amount")

    @api.model
    def _default_service_charge_on_module_install(self):
        """
        Set default service product on module installation"""
        open_configs = (
            self.env['pos.session']
            .search(['|', ('state', '!=', 'closed'), ('rescue', '=', True)])
            .mapped('config_id')
        )
        configs = self.env['pos.config'].search(
            [('id', 'not in', open_configs.ids)])
        # Do not modify configs where an opened session exists.
        product = self.env.ref("point_of_sale.product_product_consumable",
                               raise_if_not_found=False)
        for conf in configs:
            conf.service_product_id = product if (
                                                     conf.is_service_charges
                                                 ) and product and (
                                                         not product.company_id or product.company_id == conf.company_id
                                                 ) else False

    def open_ui(self):
        """
        Overridden to check if service product is set when service charge is enabled"""
        for config in self:
            if not self.current_session_id and (
                    config.is_service_charges
            ) and not config.service_product_id:
                raise UserError(self.env._(
                    'A discount product is needed to use the Service Charge '
                    'feature. Go to Point of Sale > Configuration > Settings '
                    'to set it.'))
        return super().open_ui()

    def _get_special_products(self):
        """ Overridden to add service product to the list of special products"""
        res = super()._get_special_products()
        configs = self.env['pos.config'].search(
            [('service_product_id', '!=', False)])
        return res | configs.mapped('service_product_id')


    image = fields.Binary(help="Set logo image for viewing it"
                                               "in POS Screen and Receipt")
    logo_option = fields.Selection(
        selection=[
            ('pos', 'Show POS Logo Only'),
            ('company', 'Show Company Logo Only'),
            ('both', 'Show Both POS and Company Logos')],
        string="Receipt Logo Option",
        default='pos',
        help="Choose which logo(s) to display on the printed POS receipt.")

    user_ids = fields.Many2many('res.users', 'pos_config_res_users_rel',
                                'pos_config_id', 'res_users_id',
                                string='Allowed Users',
                                help="The users who are allowed to access this"
                                     "POS.")
    is_allowed_pos = fields.Boolean(compute='_compute_is_allowed_pos',
                                   search='_search_is_allowed_pos')
    customer_details = fields.Boolean(
                                      help="By Enabling the customer details"
                                           " in pos receipt")
    customer_name = fields.Boolean(
                                   help="By Enabling the customer name "
                                        "in pos receipt")
    customer_address = fields.Boolean(
                                      help="By Enabling the customer Address "
                                           "in pos receipt")
    customer_mobile = fields.Boolean(
                                     help="By Enabling the customer mobile "
                                          "in pos receipt")
    customer_phone = fields.Boolean(
                                    help="By Enabling the customer phone "
                                         "in pos receipt")
    customer_email = fields.Boolean(
                                    help="By Enabling the customer email "
                                         "in pos receipt")
    customer_vat = fields.Boolean(string="Customer VAT",
                                  help="By Enabling the customer vat details "
                                       "in pos receipt")
    show_order_barcode = fields.Boolean(
        string="Order Barcode",
        help="Show the order barcode on the POS receipt")
    show_invoice_number = fields.Boolean(
        string="Invoice Number",
        help="Show the invoice number on the POS receipt")

    custom_tip_percentage = fields.Float(
        compute='_compute_custom_tip_percentage',
        help="Tip percentage configured in the POS settings")

    def _compute_custom_tip_percentage(self):
        """Global tip percentage, stored as a system parameter by the
        settings page."""
        value = float(self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_pos_kit.custom_tip_percentage') or 0.0)
        for rec in self:
            rec.custom_tip_percentage = value

    @api.model
    def _load_pos_data_fields(self, config):
        """Make the module fields available in the POS frontend. Without
        this the service charge settings (and the logo / customer receipt
        options) are not loaded, so ``pos.config.is_service_charges`` is
        always undefined and the Service Charge button never appears."""
        fields_list = super()._load_pos_data_fields(config)
        # An empty list means that the standard loads every field already.
        if fields_list:
            fields_list += [
                name for name in (
                    'is_service_charges', 'visibility_type', 'service_charge',
                    'service_product_id', 'service_charge_type',
                    'image', 'logo_option', 'customer_details',
                    'customer_name', 'customer_address', 'customer_mobile',
                    'customer_phone', 'customer_email', 'customer_vat',
                    'show_order_barcode', 'show_invoice_number',
                    'custom_tip_percentage',
                ) if name not in fields_list
            ]
        return fields_list

    @api.model
    def _load_pos_data_read(self, records, config):
        read_records = super()._load_pos_data_read(records, config)
        if not read_records:
            return read_records
        record = read_records[0]
        # Custom tip percentage is a global setting (ir.config_parameter)
        record['custom_tip_percentage'] = float(
            self.env['ir.config_parameter'].sudo().get_param(
                'all_in_one_pos_kit.custom_tip_percentage') or 0.0)
        if config.customer_details:
            record['customer_name'] = config.customer_name
            record['customer_address'] = config.customer_address
            record['customer_mobile'] = config.customer_mobile
            record['customer_phone'] = config.customer_phone
            record['customer_email'] = config.customer_email
            record['customer_vat'] = config.customer_vat
        return read_records

    def _compute_is_session(self):
        """To check the service charge is set up for session wise or
        globally"""
        is_session = self.env['ir.config_parameter'].sudo().get_param(
            'all_in_one_pos_kit.visibility') == 'session'
        for rec in self:
            rec.is_session = is_session

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
