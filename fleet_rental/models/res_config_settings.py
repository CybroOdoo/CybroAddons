# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit configuration settings"""
    _inherit = 'res.config.settings'

    def _get_default_product(self):
        try:
            return self.env.ref('fleet_rental.fleet_service_product').id
        except ValueError:
            return False

    fleet_service_product_id = fields.Many2one(
        comodel_name='product.template',
        string="Product",
        config_parameter='fleet_rental.fleet_service_product_id',
        default=_get_default_product,
        help="Fleet Service Product")

    @api.model
    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'fleet_rental.fleet_service_product_id',
            self.fleet_service_product_id.id or False
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        product_id = self.env['ir.config_parameter'].sudo().get_param(
            'fleet_rental.fleet_service_product_id'
        )
        res.update(
            fleet_service_product_id=int(product_id) if product_id else False
        )
        return res
