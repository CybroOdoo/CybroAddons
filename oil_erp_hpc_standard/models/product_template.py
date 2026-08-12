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

class ProductTemplate(models.Model):
    """
    Product-level HPM fields.

    New in v3:
      - hpm_api_product_group and gas composition fields mirroring
        product.category, allowing product-level override.
      - hpm_vcf_warnings: computed text showing any range violations.
      - _HPM_CONFIG_FIELDS extended with new fields so category defaults
        flow through correctly.
    """
    _inherit = 'product.template'

    # -------------------------------------------------------------------------
    # Master flag + standard selection
    # -------------------------------------------------------------------------
    is_hpm_enabled = fields.Boolean(string='HPM Correction', default=False, help="Enable or activate this option to apply 'hpm correction' status to the record.")
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
        default='ASTM-D1250', help="Select the appropriate classification or category for 'standardisation type'.",
    )

    # -------------------------------------------------------------------------
    # API product group (NEW)
    # -------------------------------------------------------------------------
    hpm_api_product_group = fields.Selection(
        [
            ('A', 'Group A — Crude Oils'),
            ('B', 'Group B — Fuel Oils'),
            ('C', 'Group C — Jet Fuels / Kerosene'),
            ('D', 'Group D — Transition Zone'),
            ('E', 'Group E — Gasolines / Naphtha'),
            ('F', 'Group F — Lubricating Oils'),
        ],
        string='API Product Group',
        default='A',
        help="API MPMS 11.1 product group controlling K0 in the alpha60 formula.",
    )

    # -------------------------------------------------------------------------
    # Reference conditions
    # -------------------------------------------------------------------------
    hpm_standard_temperature = fields.Float(
        string='Standard Temperature (°F)', digits=(6, 2), default=60.0, help="The temperature of the product measured during volume reading, in Fahrenheit.")
    hpm_standard_pressure = fields.Float(
        string='Standard Pressure (psi)', digits=(6, 2), default=0.0, help="The pressure of the product measured during volume reading, in psi.")
    hpm_standard_api_gravity = fields.Float(
        string='Standard API Gravity', digits=(5, 2), default=34.0, help="The API gravity of the petroleum product used to determine its standard quality and volume.")

    # -------------------------------------------------------------------------
    # Quality
    # -------------------------------------------------------------------------
    hpm_water_content = fields.Float(
        string='Water Content / BSW (%)', digits=(6, 3), default=0.0, help="The percentage of basic sediment and water present in the liquid, used to calculate net volume.")
    hpm_sulfur_content = fields.Float(
        string='Sulfur Content (%)', digits=(6, 4), default=0.0, help="The mass percentage of sulfur present in the product, used for quality grading.")

    # -------------------------------------------------------------------------
    # Gas composition mole fractions (NEW — product-level override)
    # -------------------------------------------------------------------------
    hpm_gas_y_ch4  = fields.Float(string='CH₄ mol%', digits=(6, 4), default=90.0, help="Specify the numerical measurement, volume, or financial amount for 'ch₄ mol%'.")
    hpm_gas_y_c2h6 = fields.Float(string='C₂H₆ mol%', digits=(6, 4), default=5.0, help="Specify the numerical measurement, volume, or financial amount for 'c₂h₆ mol%'.")
    hpm_gas_y_c3h8 = fields.Float(string='C₃H₈ mol%', digits=(6, 4), default=1.0, help="Specify the numerical measurement, volume, or financial amount for 'c₃h₈ mol%'.")
    hpm_gas_y_co2  = fields.Float(string='CO₂ mol%', digits=(6, 4), default=1.0, help="Specify the numerical measurement, volume, or financial amount for 'co₂ mol%'.")
    hpm_gas_y_n2   = fields.Float(string='N₂ mol%', digits=(6, 4), default=2.0, help="Specify the numerical measurement, volume, or financial amount for 'n₂ mol%'.")
    hpm_gas_y_h2s  = fields.Float(string='H₂S mol%', digits=(6, 4), default=1.0, help="Specify the numerical measurement, volume, or financial amount for 'h₂s mol%'.")

    # -------------------------------------------------------------------------
    # Observed (playground) inputs + outputs
    # -------------------------------------------------------------------------
    hpm_observed_temperature = fields.Float(
        string='Observed Temperature (°F)', digits=(6, 2), default=60.0, help="The temperature of the product measured during volume reading, in Fahrenheit.")
    hpm_observed_pressure = fields.Float(
        string='Observed Pressure (psi)', digits=(6, 2), default=0.0, help="The pressure of the product measured during volume reading, in psi.")
    hpm_observed_api_gravity = fields.Float(
        string='Observed API Gravity', digits=(5, 2), default=34.0, help="The API gravity of the petroleum product used to determine its standard quality and volume.")
    hpm_observed_volume = fields.Float(
        string='Observed Volume', digits=(12, 4), default=1.0, help="The volume of the product measured during physical operations.")

    hpm_ctl = fields.Float(
        string='CTL', digits=(10, 6),
        compute='_compute_hpm_calculation_outputs', store=True, help="Specify the numerical measurement, volume, or financial amount for 'ctl'.")
    hpm_cpl = fields.Float(
        string='CPL', digits=(10, 6),
        compute='_compute_hpm_calculation_outputs', store=True, help="Specify the numerical measurement, volume, or financial amount for 'cpl'.")
    hpm_vcf = fields.Float(
        string='VCF', digits=(10, 6),
        compute='_compute_hpm_calculation_outputs', store=True, help="Specify the numerical measurement, volume, or financial amount for 'vcf'.")
    hpm_compressibility = fields.Float(
        string='Compressibility', digits=(10, 6),
        compute='_compute_hpm_calculation_outputs', store=True, help="Specify the numerical measurement, volume, or financial amount for 'compressibility'.")
    hpm_standard_volume = fields.Float(
        string='Standard Volume', digits=(12, 4),
        compute='_compute_hpm_calculation_outputs', store=True, help="The volume of the product measured during physical operations.")
    hpm_vcf_warnings = fields.Text(
        string='VCF Warnings',
        compute='_compute_hpm_calculation_outputs', store=True,
        help="Range or validity warnings from the last VCF computation.",
    )

    _HPM_CONFIG_FIELDS = (
        'is_hpm_enabled',
        'hpm_standardisation',
        'hpm_api_product_group',
        'hpm_standard_temperature',
        'hpm_standard_pressure',
        'hpm_standard_api_gravity',
        'hpm_water_content',
        'hpm_sulfur_content',
        'hpm_gas_y_ch4',
        'hpm_gas_y_c2h6',
        'hpm_gas_y_c3h8',
        'hpm_gas_y_co2',
        'hpm_gas_y_n2',
        'hpm_gas_y_h2s',
    )

    # =========================================================================
    # Category-default plumbing
    # =========================================================================
    def _hpm_values_from_category(self, categ):
        """Executes the 'hpm values from category' process within the operational workflow."""
        if not categ:
            return {}
        vals = {}
        for fname in self._HPM_CONFIG_FIELDS:
            value = categ[fname]
            if isinstance(value, models.BaseModel):
                vals[fname] = value.id if value else False
            else:
                vals[fname] = value
        return vals

    @api.onchange('categ_id')
    def _onchange_categ_id_hpm_defaults(self):
        """Refreshes UI fields and updates default values dynamically when the user modifies the 'id hpm defaults' field."""
        if not self.categ_id:
            return
        if not self.is_hpm_enabled:
            for fname, value in self._hpm_values_from_category(self.categ_id).items():
                self[fname] = value

    @api.model_create_multi
    def create(self, vals_list):
        """Registers a new record in the system, validating and pre-populating standard operational defaults."""
        for vals in vals_list:
            categ_id = vals.get('categ_id')
            if not categ_id:
                continue
            categ = self.env['product.category'].browse(categ_id)
            for fname, default_val in self._hpm_values_from_category(categ).items():
                vals.setdefault(fname, default_val)
        return super().create(vals_list)

    def action_reset_hpm_to_category(self):
        """Triggers the transition of the record to proceed with the 'reset hpm to category' step in the workflow."""
        for product in self:
            if product.categ_id:
                product.write(product._hpm_values_from_category(product.categ_id))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'HPM Reset',
                'message': 'HPM fields reset to category defaults.',
                'type': 'success',
                'sticky': False,
            },
        }

    # =========================================================================
    # Playground compute
    # =========================================================================
    @api.depends(
        'is_hpm_enabled',
        'hpm_observed_temperature', 'hpm_observed_pressure',
        'hpm_observed_api_gravity', 'hpm_observed_volume',
        'hpm_standard_temperature', 'hpm_standard_pressure',
        'hpm_standard_api_gravity', 'hpm_standardisation',
        'hpm_api_product_group',
        'hpm_gas_y_ch4', 'hpm_gas_y_c2h6', 'hpm_gas_y_c3h8',
        'hpm_gas_y_co2', 'hpm_gas_y_n2', 'hpm_gas_y_h2s',
    )
    def _compute_hpm_calculation_outputs(self):
        """Calculates and updates the 'calculation outputs' value automatically based on related operational inputs."""
        engine = self.env['oil.hpm.calculation.engine']
        for product in self:
            ctl = cpl = vcf = compressibility = 1.0
            standard_volume = product.hpm_observed_volume
            warnings_text = ''
            if product.is_hpm_enabled:
                res = engine.compute_vcf(
                    config_source=product,
                    observed_temp=product.hpm_observed_temperature,
                    observed_pressure=product.hpm_observed_pressure,
                    observed_api_gravity=product.hpm_observed_api_gravity,
                    observed_volume=product.hpm_observed_volume,
                )
                ctl = res.get('ctl', 1.0)
                cpl = res.get('cpl', 1.0)
                vcf = res.get('vcf', 1.0)
                compressibility = res.get('compressibility', 1.0)
                standard_volume = res.get('standard_volume', product.hpm_observed_volume)
                warnings = res.get('warnings', [])
                warnings_text = '\n'.join(warnings) if warnings else ''
            product.hpm_ctl = ctl
            product.hpm_cpl = cpl
            product.hpm_vcf = vcf
            product.hpm_compressibility = compressibility
            product.hpm_standard_volume = standard_volume
            product.hpm_vcf_warnings = warnings_text

    # Convenience for engine call — produce gas comp fraction dict
    def _gas_comp_fractions(self):
        """Executes the 'gas comp fractions' process within the operational workflow."""
        self.ensure_one()
        total = (
            self.hpm_gas_y_ch4 + self.hpm_gas_y_c2h6 + self.hpm_gas_y_c3h8
            + self.hpm_gas_y_co2 + self.hpm_gas_y_n2 + self.hpm_gas_y_h2s
        ) or 100.0
        return {
            'y_ch4':  self.hpm_gas_y_ch4  / total,
            'y_c2h6': self.hpm_gas_y_c2h6 / total,
            'y_c3h8': self.hpm_gas_y_c3h8 / total,
            'y_co2':  self.hpm_gas_y_co2  / total,
            'y_n2':   self.hpm_gas_y_n2   / total,
            'y_h2s':  self.hpm_gas_y_h2s  / total,
        }
