#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


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
        default=lambda self: self._get_default_product(),
        help="Fleet Service Product")
