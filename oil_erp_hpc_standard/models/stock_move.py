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

from odoo import fields, models

class StockMove(models.Model):
    """Extend stock.move to preserve HPM physical measurement audit data.

    hpm_vcf_warnings (new in v3): stores any range validation messages
    produced at the time of VCF computation so they are permanently
    visible on the stock move record for audit purposes.
    """
    _inherit = 'stock.move'

    hpm_temperature = fields.Float(
        string='Observed Temperature (°F)', digits=(6, 2),
        help="Observed temperature recorded at custody transfer.",
    )
    hpm_pressure = fields.Float(
        string='Observed Pressure (psi)', digits=(6, 2),
        help="Observed operating pressure recorded at custody transfer.",
    )
    hpm_api_gravity = fields.Float(
        string='Observed API Gravity', digits=(5, 2),
        help="Observed API gravity of the liquid/gas.",
    )
    hpm_observed_qty = fields.Float(
        string='Observed Volume (raw)', digits=(12, 4),
        help="Measured raw volume before HPM correction is applied.",
    )
    hpm_vcf = fields.Float(
        string='HPM Correction (VCF)', digits=(7, 5),
        help="Volume Correction Factor applied to this move.",
    )
    hpm_water_content = fields.Float(
        string='Water / BSW (%)', digits=(6, 3),
        help="Basic Sediment and Water content at time of move.",
    )
    hpm_sulfur_content = fields.Float(
        string='Sulfur Content (%)', digits=(6, 4),
        help="Total sulfur content at time of move.",
    )
    hpm_vcf_warnings = fields.Text(
        string='VCF Range Warnings',
        help=(
            "Range or validity warnings recorded at the time the VCF was "
            "computed. Non-empty means one or more inputs fell outside the "
            "standard's defined applicability range."
        ),
    )
