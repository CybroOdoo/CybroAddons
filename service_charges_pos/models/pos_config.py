# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
    """ Inherits POS Configuration """
    _inherit = 'pos.config'

    is_session = fields.Boolean(string="Session",
                                compute='_compute_is_session',
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
    service_product_id = fields.Many2one(
        'product.product',
        string='Service Product',
        domain="[('available_in_pos', '=', "
               "True),"
               "('sale_ok', '=', True), "
               "('type', '=', 'service')]",
        help="Service product")

    has_service_charge = fields.Boolean(string='Service charge',
                                        compute="_compute_has_service_charge")
    config_visibility = fields.Selection([
        ('global', 'Global'),
        ('session', 'Session')],
        string="Visibility", compute="_compute_config_visibility",
        help='Setup the Service charge globally or per session')
    config_selection = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')],
        string='Selection type', compute="_compute_config_selection",
        help='Set the service charge as a amount or percentage')
    config_charge = fields.Float(string='Charge',
                                 compute="_compute_config_charge",
                                 help='Set a default service charge globally')
    config_product_id = fields.Many2one('product.product',
                                        string='Service Product',
                                        domain="[('available_in_pos', '=', "
                                               "True),"
                                               "('sale_ok', '=', True), "
                                               "('type', '=', 'service')]",
                                        compute="_compute_config_product",
                                        help='Set a service product globally')

    def _compute_is_session(self):
        """ To check the service charge is set for session wise or globally """
        check_session = self.env['ir.config_parameter'].sudo().get_param(
            'service_charges_pos.visibility')
        if check_session == 'session':
            self.is_session = True
        else:
            self.is_session = False

    @api.onchange('is_service_charges')
    def onchange_is_service_charges(self):
        """ When the service charge is enabled set the service product and
        amount by default per session. """
        if self.is_service_charges:
            if not self.service_product_id:
                domain = [('available_in_pos', '=', True),
                          ('sale_ok', '=', True), ('type', '=', 'service')]
                self.service_product_id = self.env['product.product'].search(
                    domain, limit=1)
                self.service_charge = 10.0
        else:
            self.service_product_id = False
            self.service_charge = 0.0

    def _compute_has_service_charge(self):
        """ To check if service charge is enabled from settings """
        if self.env['ir.config_parameter'].sudo().get_param(
                'service_charges_pos.enable_service_charge'):
            self.has_service_charge = True
        else:
            self.has_service_charge = False

    def _compute_config_visibility(self):
        """ To obtain service charge type from res.config.settings """
        res = self.env['ir.config_parameter'].sudo()
        if res.get_param(
                'service_charges_pos.enable_service_charge'):
            settings_visibility = res.get_param(
                'service_charges_pos.visibility')
            self.config_visibility = settings_visibility
        else:
            self.config_visibility = ''

    def _compute_config_charge(self):
        """ To obtain service charge from res.config.settings """
        res = self.env['ir.config_parameter'].sudo()
        if res.get_param(
                'service_charges_pos.enable_service_charge'):
            charge = res.get_param(
                'service_charges_pos.global_charge')
            self.config_charge = charge
        else:
            self.config_charge = 0

    def _compute_config_selection(self):
        """ To obtain service charge mode from res.config.settings """
        res = self.env['ir.config_parameter'].sudo()
        if res.get_param(
                'service_charges_pos.enable_service_charge'):
            selection = res.get_param(
                'service_charges_pos.global_selection')
            self.config_selection = selection
        else:
            self.config_selection = ''

    def _compute_config_product(self):
        """ To obtain service charge product from res.config.settings """
        res = self.env['ir.config_parameter'].sudo()
        if res.get_param(
                'service_charges_pos.enable_service_charge'):
            product_id = res.get_param(
                'service_charges_pos.global_product_id')
            product = self.env['product.template'].browse(int(product_id))
            self.config_product_id = product.id
        else:
            self.config_product_id = ''
