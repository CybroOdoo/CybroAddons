# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
    ''' Inherit res.config.settings to add service charges fields '''
    _inherit = 'res.config.settings'

    # pos.config fields
    pos_is_service_charges = fields.Boolean(
        related='pos_config_id.is_service_charges', readonly=False,
    string="Service Charges", help="Enable Service Charges")
    pos_visibility_type = fields.Selection([
        ('global', 'Global'),
        ('session', 'Session')],
        related='pos_config_id.visibility_type',
        readonly=False, help="Can choose visibility of service charges.")
    pos_service_charge = fields.Float(related='pos_config_id.service_charge',
                                      readonly=False, help="Charge need to apply")
    pos_service_product_id = fields.Many2one(
        'product.product',
        compute='_compute_pos_service_product_id', store=True, readonly=False,
        domain="[('type', '=', 'service')]")
    pos_service_charge_type = fields.Selection([
        ('amount', 'Amount'),
        ('percentage', 'Percentage')],
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
