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


class PosConfig(models.Model):
    """Inherited POS Configuration"""
    _inherit = 'pos.config'

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

    def _compute_check_session(self):
        """To check the service charge is setup for session wise or globally"""
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