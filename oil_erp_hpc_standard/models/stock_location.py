# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from odoo import api, fields, models

class StockLocation(models.Model):
    """Extend stock.location to define storing/standard conditions linked
    directly to a Product Category (Storage Category)."""
    _inherit = 'stock.location'

    hpm_category_id = fields.Many2one(
        'product.category',
        string='Storage Category',
        help='Category of product stored in this tank. Standard reference conditions are inherited from this category.'
    )

    # Change base_temperature_f to storing temperature and relate to product category standard temp
    base_temperature_f = fields.Float(
        string='Storing Temperature (°F)',
        related='hpm_category_id.hpm_standard_temperature',
        store=True,
        help='Storing temperature related to the product category standard temperature.'
    )

    storing_pressure = fields.Float(
        string='Storing Pressure (psi)',
        related='hpm_category_id.hpm_standard_pressure',
        store=True,
        help='Storing pressure related to the product category standard pressure.'
    )

    storing_api_gravity = fields.Float(
        string='Storing API Gravity',
        related='hpm_category_id.hpm_standard_api_gravity',
        store=True,
        help='Storing API gravity related to the product category standard API gravity.'
    )

    temp_warning = fields.Char(
        compute='_compute_telemetry_warnings',
        help='Warning message when current temperature differs from standard/storing temperature.'
    )
    press_warning = fields.Char(
        compute='_compute_telemetry_warnings',
        help='Warning message when current pressure differs from standard/storing pressure.'
    )
    api_warning = fields.Char(
        compute='_compute_telemetry_warnings',
        help='Warning message when current API gravity differs from standard/storing API gravity.'
    )

    @api.depends(
        'current_temperature_f', 'base_temperature_f',
        'current_pressure', 'storing_pressure',
        'current_api_gravity', 'storing_api_gravity'
    )
    def _compute_telemetry_warnings(self):
        """Calculates and updates the 'warnings' value automatically based on related operational inputs."""
        for rec in self:
            if rec.current_temperature_f and abs(rec.current_temperature_f - rec.base_temperature_f) > 0.01:
                rec.temp_warning = f"⚠️ Temperature ({rec.current_temperature_f}°F) differs from storing ({rec.base_temperature_f}°F)"
            else:
                rec.temp_warning = False

            if rec.current_pressure and abs(rec.current_pressure - rec.storing_pressure) > 0.01:
                rec.press_warning = f"⚠️ Pressure ({rec.current_pressure} psi) differs from storing ({rec.storing_pressure} psi)"
            else:
                rec.press_warning = False

            if rec.current_api_gravity and abs(rec.current_api_gravity - rec.storing_api_gravity) > 0.01:
                rec.api_warning = f"⚠️ API Gravity ({rec.current_api_gravity}) differs from storing ({rec.storing_api_gravity})"
            else:
                rec.api_warning = False
