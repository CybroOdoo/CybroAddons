# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu (odoo@cybrosys.com)
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
################################################################################


from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited Configuration Settings"""
    _inherit = "res.config.settings"

    enable_service_charge = fields.Boolean(string="Service Charges",
                                           config_parameter="service_charges_pos.enable_service_charge",
                                           help="Enable to add service charge")
    visibility = fields.Selection([
        ('global', 'Global'),
        ('session', 'Session')],
        default='global', string="Visibility",
        config_parameter="service_charges_pos.visibility",
        help='Setup the Service charge globally or per session')
    global_selection = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')],
        string='Type', default='amount',
        config_parameter="service_charges_pos.global_selection",
        help='Set the service charge as a amount or percentage')
    global_charge = fields.Float(string='Service Charge',
                                 config_parameter="service_charges_pos.global_charge",
                                 help='Set a default service charge globally')
    global_product_id = fields.Many2one('product.product',
                                        string='Service Product',
                                        domain="[('available_in_pos', '=', "
                                               "True),"
                                               "('sale_ok', '=', True), "
                                               "('type', '=', 'service')]",
                                        config_parameter="service_charges_pos"
                                                         ".global_product_id",
                                        help='Set a service product globally')

    @api.onchange('enable_service_charge')
    def onchange_enable_service_charge(self):
        """When the service charge is enabled set service product and amount
        by default in globally"""
        if self.enable_service_charge:
            if not self.global_product_id:
                domain = [('available_in_pos', '=', True),
                          ('sale_ok', '=', True), ('type', '=', 'service')]
                self.global_product_id = self.env[
                    'product.product'].search(
                    domain, limit=1)
                self.global_charge = 10.0
        else:
            self.global_product_id = False
            self.global_charge = 0.0

