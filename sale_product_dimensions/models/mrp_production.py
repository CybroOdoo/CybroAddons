# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class MrpProduction(models.Model):
    """ Inherits the Production model to include
        product dimension fields."""
    _inherit = 'mrp.production'

    length_mm = fields.Float(
        string="Length (mm)",
        help="The length of the product in millimeters."
    )
    width_mm = fields.Float(
        string="Width (mm)",
        help="The width of the product in millimeters."
    )
    area_m2 = fields.Float(
        string="Area (m²)",
        help="The area of the product in square meters, "
             "calculated based on length and width.",
        compute="_compute_area"
    )
    price_per_m2 = fields.Float(
        string="Price / m²",
        help="The price of the product per square meter."
    )

    @api.depends('length_mm', 'width_mm')
    def _compute_area(self):
        """Compute the area in square meters based on length and width."""
        for mo in self:
            if mo.length_mm and mo.width_mm:
                mo.area_m2 = (mo.length_mm * mo.width_mm) / 1000000.0
            else:
                mo.area_m2 = 0.0
