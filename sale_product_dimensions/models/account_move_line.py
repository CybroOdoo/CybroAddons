# -*- coding: utf-8 -*-
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
        digits=(16, 4),
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
        for line in self:
            if line.length_mm and line.width_mm:
                line.area_m2 = (line.length_mm * line.width_mm) / 1000000.0
            else:
                line.area_m2 = 0.0
