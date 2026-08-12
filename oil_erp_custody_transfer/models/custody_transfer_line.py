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
from odoo.exceptions import ValidationError
from odoo.tools.translate import _

class CustodyTransferLine(models.Model):
    """Product-level detail for a custody transfer.

    All measurement math is delegated to the shared service on
    oil.hpm.calculation.engine.compute_vcf(). No formulas live in this file.
    All measurement fields follow the HPM naming convention
    (`hpm_observed_*`) for symmetry with product.template, project.task,
    stock.move and the production wizard.
    """
    _name = "custody.transfer.line"
    _description = "Custody Transfer Line"
    _order = "transfer_id, sequence, id"

    transfer_id = fields.Many2one(
        "custody.transfer",
        string="Transfer", required=True,
        ondelete="cascade", index=True,
        help="Parent custody transfer this line belongs to.",
    )
    sequence = fields.Integer(string="Sequence", default=10, help="A sequence number used to define the display order of this item in lists.")
    product_id = fields.Many2one(
        "product.product", string="Product", required=True,
        help="Link this transaction or record to the corresponding 'product' reference.",
    )
    product_uom_id = fields.Many2one(
        "uom.uom", string="UoM", required=True,
        help="Unit of measure for all quantities on this line.",
    )

    # -------------------------------------------------------------------------
    # Quantities
    # -------------------------------------------------------------------------
    planned_qty = fields.Float(
        string="Planned Qty", default=0.0,
        help="Quantity scheduled for transfer when the document was drafted.",
    )
    actual_qty = fields.Float(
        string="Actual Qty", default=0.0,
        help="Final operator-confirmed quantity that actually changed custody.",
    )
    loss_qty = fields.Float(
        string="Loss", compute="_compute_loss_gain", store=True,
        help="Positive quantity short of the planned amount.",
    )
    gain_qty = fields.Float(
        string="Gain", compute="_compute_loss_gain", store=True,
        help="Positive quantity above the planned amount.",
    )
    variance_qty = fields.Float(
        string="Variance", compute="_compute_loss_gain", store=True,
        help="Signed difference between actual and planned quantities.",
    )
    notes = fields.Char(string="Notes", help="Additional comments, details, or operational remarks about this record.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, help="The company managing this operational record or transaction.")


    # -------------------------------------------------------------------------
    # HPM measurement inputs (°F / psi, matching HPM module and SCADA tanks)
    # -------------------------------------------------------------------------
    hpm_observed_temperature = fields.Float(
        string="Observed Temperature (°F)",
        digits=(6, 2),
        help="Product temperature at measurement. °F, matches stock.move "
             "and SCADA tank readings.",
    )
    hpm_observed_pressure = fields.Float(
        string="Observed Pressure (psi)",
        digits=(8, 2),
        help="Product pressure at measurement, in psi.",
    )
    hpm_observed_api_gravity = fields.Float(
        string="Observed API Gravity",
        digits=(6, 2),
        help="API gravity at observed temperature.",
    )
    hpm_density_at_15c = fields.Float(
        string="Density @ 15°C (kg/m³)",
        digits=(8, 3),
        help="Derived from API gravity (ASTM D1250 / D287). Auto-filled "
             "when API gravity is entered.",
    )
    hpm_water_content = fields.Float(
        string="Water / BSW (%)",
        digits=(6, 3),
        help="Basic Sediment and Water content as a percentage. "
             "Net Standard Volume = Standard Volume × (1 − Water%/100). "
             "Defaults from the product (which inherits from its category).",
    )
    hpm_sulfur_content = fields.Float(
        string="Sulfur Content (%)",
        digits=(6, 4),
        help="Total sulfur content as a percentage by mass. "
             "Defaults from the product.",
    )

    # -------------------------------------------------------------------------
    # HPM outputs (computed via shared service)
    # -------------------------------------------------------------------------
    hpm_ctl = fields.Float(
        string="CTL",
        compute="_compute_hpm_outputs", store=True,
        digits=(10, 6),
        help="Temperature correction factor (per ASTM D1250 / OIML R117 / GPA TP-27 branch).",
    )
    hpm_cpl = fields.Float(
        string="CPL",
        compute="_compute_hpm_outputs", store=True,
        digits=(10, 6),
        help="Specify the numerical measurement, volume, or financial amount for 'cpl'.",
    )
    hpm_vcf = fields.Float(
        string="VCF",
        compute="_compute_hpm_outputs", store=True,
        digits=(10, 6),
        help="Volume Correction Factor computed from the line's product "
             "(which inherits standardisation and reference conditions from "
             "its category). Equals 1.0 when no observed temperature is "
             "provided or the product is not HPM-enabled.",
    )
    hpm_compressibility = fields.Float(
        string="Compressibility",
        compute="_compute_hpm_outputs", store=True,
        digits=(10, 6),
        help="Specify the numerical measurement, volume, or financial amount for 'compressibility'.",
    )
    hpm_standard_volume = fields.Float(
        string="Standard Volume",
        compute="_compute_hpm_outputs", store=True,
        digits=(16, 4),
        help="Actual Qty × VCF — the volume corrected to standard conditions.",
    )
    hpm_net_standard_volume = fields.Float(
        string="Net Standard Volume",
        compute="_compute_hpm_net_standard_volume", store=True,
        digits=(16, 4),
        help="Standard Volume × (1 − Water%/100). The commercially "
             "relevant net quantity.",
    )
    hpm_required_actual_qty = fields.Float(
        string="Required Actual Qty",
        compute="_compute_hpm_required_actual_qty", store=True,
        digits=(16, 4),
        help="The actual observed quantity required to yield a net standard volume equal to the planned (demand) quantity.",
    )

    # =========================================================================
    # Onchange helpers
    # =========================================================================
    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Default the UoM and pull quality defaults from the product."""
        for line in self:
            if not line.product_id:
                continue
            if not line.product_uom_id:
                line.product_uom_id = line.product_id.uom_id
            # Quality defaults from product (product inherits from category).
            if not line.hpm_water_content:
                line.hpm_water_content = line.product_id.hpm_water_content
            if not line.hpm_sulfur_content:
                line.hpm_sulfur_content = line.product_id.hpm_sulfur_content
            
            # Check if HPM is enabled for this product/category
            is_hpm = line.product_id.is_hpm_enabled or (
                line.product_id.categ_id and line.product_id.categ_id.is_hpm_enabled
            )
            if is_hpm:
                if not line.hpm_observed_temperature:
                    line.hpm_observed_temperature = (
                        line.product_id.hpm_observed_temperature
                        or (line.product_id.categ_id and line.product_id.categ_id.hpm_standard_temperature)
                        or 60.0
                    )
                if not line.hpm_observed_pressure:
                    line.hpm_observed_pressure = (
                        line.product_id.hpm_observed_pressure
                        or (line.product_id.categ_id and line.product_id.categ_id.hpm_standard_pressure)
                        or 0.0
                    )
                if not line.hpm_observed_api_gravity:
                    line.hpm_observed_api_gravity = (
                        line.product_id.hpm_observed_api_gravity
                        or (line.product_id.categ_id and line.product_id.categ_id.hpm_standard_api_gravity)
                        or 34.0
                    )

    @api.onchange("hpm_observed_api_gravity")
    def _onchange_api_gravity(self):
        """Auto-fill density at 15°C from API gravity (ASTM D287)."""
        if self.hpm_observed_api_gravity:
            sg = 141.5 / (self.hpm_observed_api_gravity + 131.5)
            self.hpm_density_at_15c = round(sg * 999.016, 3)

    @api.onchange("hpm_density_at_15c")
    def _onchange_density_at_15c(self):
        """Auto-fill API gravity from density at 15°C."""
        if self.hpm_density_at_15c and self.hpm_density_at_15c > 0:
            sg = self.hpm_density_at_15c / 999.016
            if sg > 0:
                self.hpm_observed_api_gravity = round(141.5 / sg - 131.5, 2)

    @api.onchange("product_id", "transfer_id.measurement_method",
                  "transfer_id.source_location_id")
    def _onchange_scada_auto(self):
        """Fetch temperature and pressure from the source location if the
        transfer is set to Auto measurement and the source is a SCADA tank.
        After the HPM merge, values pass through in °F / psi unchanged."""
        if self.transfer_id and not self.transfer_id._is_scada_installed():
            return
        for line in self:
            if not line.transfer_id or line.transfer_id.measurement_method != 'auto':
                continue
            if (line.transfer_id.picking_type_id
                    and line.transfer_id.picking_type_id.code == 'incoming'):
                continue
            location = line.transfer_id.source_location_id
            if not location:
                continue
            location_db = line.env["stock.location"].browse(
                location._origin.id or location.id)
            if not location_db.is_storage_tank:
                continue
            if location_db.current_temperature_f:
                line.hpm_observed_temperature = location_db.current_temperature_f
            if location_db.current_pressure:
                line.hpm_observed_pressure = location_db.current_pressure

    # =========================================================================
    # Compute methods
    # =========================================================================
    @api.depends("planned_qty", "actual_qty")
    def _compute_loss_gain(self):
        """Calculates and updates the 'gain' value automatically based on related operational inputs."""
        for line in self:
            variance = line.actual_qty - line.planned_qty
            line.variance_qty = variance
            line.loss_qty = -variance if variance < 0 else 0.0
            line.gain_qty = variance if variance > 0 else 0.0

    @api.depends(
        "actual_qty",
        "hpm_observed_temperature",
        "hpm_observed_pressure",
        "hpm_observed_api_gravity",
        "product_id",
        "product_id.is_hpm_enabled",
        "product_id.categ_id.is_hpm_enabled",
        "product_id.hpm_standardisation",
        "product_id.hpm_standard_temperature",
        "product_id.hpm_standard_pressure",
        "product_id.hpm_standard_api_gravity",
        "product_id.categ_id.hpm_standardisation",
        "product_id.categ_id.hpm_standard_temperature",
        "product_id.categ_id.hpm_standard_pressure",
        "product_id.categ_id.hpm_standard_api_gravity",
    )
    def _compute_hpm_outputs(self):
        """Delegate to the shared HPM compute_vcf service.

        The line's product is the configuration source — product values
        default from the category but can be individually overridden, and we
        want any per-product override to be honoured. Fall back to the category
        if the product is not explicitly HPM-enabled.
        """
        engine = self.env['oil.hpm.calculation.engine']
        for line in self:
            line.hpm_ctl = 1.0
            line.hpm_cpl = 1.0
            line.hpm_vcf = 1.0
            line.hpm_compressibility = 1.0
            line.hpm_standard_volume = line.actual_qty

            product = line.product_id
            if product and (product.is_hpm_enabled or (product.categ_id and product.categ_id.is_hpm_enabled)):
                config_source = product if product.is_hpm_enabled else product.categ_id
                res = engine.compute_vcf(
                    config_source=config_source,
                    observed_temp=line.hpm_observed_temperature,
                    observed_pressure=line.hpm_observed_pressure,
                    observed_api_gravity=line.hpm_observed_api_gravity,
                    observed_volume=line.actual_qty,
                )
                line.hpm_ctl = res.get('ctl', 1.0)
                line.hpm_cpl = res.get('cpl', 1.0)
                line.hpm_vcf = res.get('vcf', 1.0)
                line.hpm_compressibility = res.get('compressibility', 1.0)
                line.hpm_standard_volume = res.get('standard_volume', line.actual_qty)

    @api.depends("hpm_standard_volume", "hpm_water_content")
    def _compute_hpm_net_standard_volume(self):
        """Calculates and updates the 'net standard volume' value automatically based on related operational inputs."""
        for line in self:
            water_fraction = (line.hpm_water_content or 0.0) / 100.0
            water_fraction = max(0.0, min(1.0, water_fraction))
            line.hpm_net_standard_volume = round(
                line.hpm_standard_volume * (1.0 - water_fraction), 4)

    @api.depends("planned_qty", "hpm_vcf", "hpm_water_content")
    def _compute_hpm_required_actual_qty(self):
        """Calculates and updates the 'required actual qty' value automatically based on related operational inputs."""
        for line in self:
            water_fraction = (line.hpm_water_content or 0.0) / 100.0
            water_fraction = max(0.0, min(1.0, water_fraction))
            net_vcf = (line.hpm_vcf or 1.0) * (1.0 - water_fraction)
            if net_vcf > 0.0:
                line.hpm_required_actual_qty = round(line.planned_qty / net_vcf, 4)
            else:
                line.hpm_required_actual_qty = line.planned_qty

    # =========================================================================
    # Constraints
    # =========================================================================
    @api.constrains("hpm_water_content")
    def _check_water_content(self):
        """Enforces validation rules to ensure 'content' meets required safety and regulatory standards."""
        for line in self:
            if line.hpm_water_content < 0 or line.hpm_water_content > 100:
                raise ValidationError(_(
                    "Water / BSW content must be between 0 and 100 percent."))

    @api.constrains("hpm_sulfur_content")
    def _check_sulfur_content(self):
        """Enforces validation rules to ensure 'content' meets required safety and regulatory standards."""
        for line in self:
            if line.hpm_sulfur_content < 0 or line.hpm_sulfur_content > 100:
                raise ValidationError(_(
                    "Sulfur content must be between 0 and 100 percent."))

    @api.model_create_multi
    def create(self, vals_list):
        """Registers a new record in the system, validating and pre-populating standard operational defaults."""
        for vals in vals_list:
            if vals.get('product_id'):
                product = self.env['product.product'].browse(vals['product_id'])
                is_hpm = product.is_hpm_enabled or (
                    product.categ_id and product.categ_id.is_hpm_enabled
                )
                if is_hpm:
                    if vals.get('hpm_observed_temperature') is None or vals.get('hpm_observed_temperature') == 0.0:
                        vals['hpm_observed_temperature'] = (
                            product.hpm_observed_temperature
                            or (product.categ_id and product.categ_id.hpm_standard_temperature)
                            or 60.0
                        )
                    if vals.get('hpm_observed_pressure') is None or vals.get('hpm_observed_pressure') == 0.0:
                        vals['hpm_observed_pressure'] = (
                            product.hpm_observed_pressure
                            or (product.categ_id and product.categ_id.hpm_standard_pressure)
                            or 0.0
                        )
                    if vals.get('hpm_observed_api_gravity') is None or vals.get('hpm_observed_api_gravity') == 0.0:
                        vals['hpm_observed_api_gravity'] = (
                            product.hpm_observed_api_gravity
                            or (product.categ_id and product.categ_id.hpm_standard_api_gravity)
                            or 34.0
                        )
                    if vals.get('hpm_water_content') is None or vals.get('hpm_water_content') == 0.0:
                        vals['hpm_water_content'] = product.hpm_water_content
                    if vals.get('hpm_sulfur_content') is None or vals.get('hpm_sulfur_content') == 0.0:
                        vals['hpm_sulfur_content'] = product.hpm_sulfur_content
        return super().create(vals_list)
