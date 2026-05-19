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


class AccountMoveLine(models.Model):
    """ Inherits the Account Move Line model to include
     product dimension fields."""
    _inherit = 'account.move.line'

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
        compute="_compute_area_m2",
        store=True,
        help="The area of the product in square meters, "
             "calculated based on length and width."
    )
    price_per_m2 = fields.Float(
        string="Price / m²",
        help="The price of the product per square meter."
    )

    @api.depends('length_mm', 'width_mm')
    def _compute_area_m2(self):
        """Compute the area in square meters based on length and width."""
        for move in self:
            if move.length_mm and move.width_mm:
                move.area_m2 = (move.length_mm * move.width_mm) / 1000000.0
            else:
                move.area_m2 = 0.0
