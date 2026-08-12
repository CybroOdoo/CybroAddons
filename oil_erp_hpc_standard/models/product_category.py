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

class ProductCategory(models.Model):
    """
    HPM configuration on product.category.

    Every product in the category inherits these defaults.
    New in v3: hpm_api_product_group (Groups A-F per API MPMS 11.1),
    gas composition mole fractions for AGA-8 Z-factor, and display
    of the applicable K0 constant for transparency.
    """
    _inherit = 'product.category'

    # -------------------------------------------------------------------------
    # Master flag + standard selection
    # -------------------------------------------------------------------------
    is_hpm_enabled = fields.Boolean(
        string='HPM Correction',
        default=False,
        help="Enable dynamic volume corrections for products in this category.",
    )
    hpm_standardisation = fields.Selection(
        [
            ('ASTM-D1250',    'ASTM D1250 (API MPMS 11.1)'),
            ('AGA-8',         'AGA-8 Natural Gas'),
            ('GPA-TP27',      'GPA TP-27 LPG / NGL'),
            ('OIML-R117',     'OIML R117 Liquid'),
            ('SAES-Y-100',    'Saudi Aramco SAES-Y-100'),
            ('AGES-SP-11-01', 'ADNOC AGES-SP-11-01'),
            ('custom',        'Custom Formula'),
        ],
        string='Standardisation Type',
        default='ASTM-D1250',
        help="Drives the formula branch used by the HPM calculation engine.",
    )
    # Compatibility alias
    hpm_standard_type = fields.Selection(
        related='hpm_standardisation', readonly=True,
        string='Standardisation Type (alias)', help="Select the appropriate classification or category for 'standardisation type (alias)'.",
    )

    # -------------------------------------------------------------------------
    # API MPMS 11.1 Product Group (NEW)
    # -------------------------------------------------------------------------
    hpm_api_product_group = fields.Selection(
        [
            ('A', 'Group A — Crude Oils (K0 = 341.0957)'),
            ('B', 'Group B — Fuel Oils / Residual (K0 = 103.8720)'),
            ('C', 'Group C — Jet Fuels / Kerosene (K0 = 330.3010)'),
            ('D', 'Group D — Transition Zone (K0 = 1489.0670)'),
            ('E', 'Group E — Gasolines / Naphtha (K0 = 192.4571)'),
            ('F', 'Group F — Lubricating Oils (polynomial alpha60)'),
        ],
        string='API Product Group',
        default='A',
        help=(
            "API MPMS Chapter 11.1 product group. Controls the K0 constant "
            "used in the alpha60 formula. Only relevant for liquid standards "
            "(ASTM D1250, OIML R117, SAES-Y-100, AGES-SP-11-01). "
            "Select the group that matches the hydrocarbon product type."
        ),
    )
    hpm_k0_display = fields.Char(
        string='K0 Constant',
        compute='_compute_k0_display',
        help="Informational: K0 value that will be used for alpha60 calculation.",
    )

    # -------------------------------------------------------------------------
    # Base / reference conditions
    # -------------------------------------------------------------------------
    hpm_standard_temperature = fields.Float(
        string='Standard Temperature (°F)', digits=(6, 2), default=60.0, help="The temperature of the product measured during volume reading, in Fahrenheit.",
    )
    hpm_standard_pressure = fields.Float(
        string='Standard Pressure (psi)', digits=(6, 2), default=0.0, help="The pressure of the product measured during volume reading, in psi.",
    )
    hpm_standard_api_gravity = fields.Float(
        string='Standard API Gravity', digits=(5, 2), default=34.0, help="The API gravity of the petroleum product used to determine its standard quality and volume.",
    )

    # -------------------------------------------------------------------------
    # Quality defaults
    # -------------------------------------------------------------------------
    hpm_water_content = fields.Float(
        string='Default Water Content / BSW (%)', digits=(6, 3), default=0.0, help="The percentage of basic sediment and water present in the liquid, used to calculate net volume.",
    )
    hpm_sulfur_content = fields.Float(
        string='Default Sulfur Content (%)', digits=(6, 4), default=0.0, help="The mass percentage of sulfur present in the product, used for quality grading.",
    )

    # -------------------------------------------------------------------------
    # Gas composition mole fractions for AGA-8 (NEW)
    # Only shown when standardisation = AGA-8
    # -------------------------------------------------------------------------
    hpm_gas_y_ch4 = fields.Float(
        string='Methane (CH₄) mol%', digits=(6, 4), default=90.0,
        help="Methane mole percent. Used in AGA-8 Z-factor calculation.",
    )
    hpm_gas_y_c2h6 = fields.Float(
        string='Ethane (C₂H₆) mol%', digits=(6, 4), default=5.0, help="Specify the numerical measurement, volume, or financial amount for 'ethane (c₂h₆) mol%'.",
    )
    hpm_gas_y_c3h8 = fields.Float(
        string='Propane (C₃H₈) mol%', digits=(6, 4), default=1.0, help="Specify the numerical measurement, volume, or financial amount for 'propane (c₃h₈) mol%'.",
    )
    hpm_gas_y_co2 = fields.Float(
        string='CO₂ mol%', digits=(6, 4), default=1.0, help="Specify the numerical measurement, volume, or financial amount for 'co₂ mol%'.",
    )
    hpm_gas_y_n2 = fields.Float(
        string='N₂ mol%', digits=(6, 4), default=2.0, help="Specify the numerical measurement, volume, or financial amount for 'n₂ mol%'.",
    )
    hpm_gas_y_h2s = fields.Float(
        string='H₂S mol%', digits=(6, 4), default=1.0, help="Specify the numerical measurement, volume, or financial amount for 'h₂s mol%'.",
    )
    hpm_gas_composition_total = fields.Float(
        string='Total mol%',
        compute='_compute_gas_total',
        digits=(6, 2),
        help="Should sum to 100%. Values are normalised internally before use.",
    )

    @api.depends(
        'hpm_gas_y_ch4', 'hpm_gas_y_c2h6', 'hpm_gas_y_c3h8',
        'hpm_gas_y_co2', 'hpm_gas_y_n2', 'hpm_gas_y_h2s',
    )
    def _compute_gas_total(self):
        """Calculates and updates the 'total' value automatically based on related operational inputs."""
        for rec in self:
            rec.hpm_gas_composition_total = (
                rec.hpm_gas_y_ch4 + rec.hpm_gas_y_c2h6 + rec.hpm_gas_y_c3h8
                + rec.hpm_gas_y_co2 + rec.hpm_gas_y_n2 + rec.hpm_gas_y_h2s
            )

    @api.depends('hpm_api_product_group')
    def _compute_k0_display(self):
        """Calculates and updates the 'display' value automatically based on related operational inputs."""
        _k0 = {
            'A': '341.0957',
            'B': '103.8720',
            'C': '330.3010',
            'D': '1489.0670',
            'E': '192.4571',
            'F': 'Polynomial (no K0)',
        }
        for rec in self:
            rec.hpm_k0_display = _k0.get(rec.hpm_api_product_group or 'A', '341.0957')

    # Convenience used by custody transfer
    def is_gas_standard(self):
        """Executes the 'is gas standard' process within the operational workflow."""
        self.ensure_one()
        return self.hpm_standardisation in ('AGA-8', 'AGA-3', 'ISO-6976')

    # Helper: produce mole fraction dict (0–1) for engine call
    def _gas_comp_fractions(self):
        """Executes the 'gas comp fractions' process within the operational workflow."""
        self.ensure_one()
        total = self.hpm_gas_composition_total or 100.0
        if total <= 0:
            total = 100.0
        return {
            'y_ch4':  self.hpm_gas_y_ch4  / total,
            'y_c2h6': self.hpm_gas_y_c2h6 / total,
            'y_c3h8': self.hpm_gas_y_c3h8 / total,
            'y_co2':  self.hpm_gas_y_co2  / total,
            'y_n2':   self.hpm_gas_y_n2   / total,
            'y_h2s':  self.hpm_gas_y_h2s  / total,
        }
