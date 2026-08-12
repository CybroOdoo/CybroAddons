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
from odoo.tools.translate import _

class ProductionWizard(models.TransientModel):
    """
    Inherit production wizard to add HPM header defaults.

    On wizard open / storage location change, header T/P and API gravity
    are auto-filled from tank telemetry or the storage location HPM category.
    """
    _inherit = 'production.wizard'

    temperature = fields.Float(
        string='Observed Temperature (°F)', digits=(6, 2), default=60.0,
        help="Average temperature for production lines. "
             "Auto-filled from tank telemetry or storage location.",
    )
    pressure = fields.Float(
        string='Observed Pressure (psi)', digits=(6, 2), default=0.0,
        help="Average operating pressure. Auto-filled from tank telemetry.",
    )
    api_gravity = fields.Float(
        string='Observed API Gravity', digits=(5, 2), default=34.0,
        help="The API gravity of the petroleum product used to determine its standard quality and volume.",
    )

    @api.model
    def default_get(self, fields_list):
        """Executes the 'default get' process within the operational workflow."""
        res = super().default_get(fields_list)
        loc_id = res.get('storage_location_id')
        if not loc_id and res.get('task_id'):
            task = self.env['project.task'].browse(res['task_id'])
            if task.project_id and task.project_id.storage_location_id:
                loc_id = task.project_id.storage_location_id.id
        if loc_id:
            loc = self.env['stock.location'].browse(loc_id)
            if getattr(loc, 'is_storage_tank', False):
                if 'temperature' in fields_list:
                    res['temperature'] = loc.base_temperature_f or 60.0
                if 'pressure' in fields_list:
                    res['pressure'] = getattr(loc, 'storing_pressure', 0.0) or 0.0
                if 'api_gravity' in fields_list:
                    res['api_gravity'] = getattr(loc, 'storing_api_gravity', 34.0) or 34.0
        return res

    @api.onchange('storage_location_id')
    def _onchange_storage_location_pull_tank_readings(self):
        """Refreshes UI fields and updates default values dynamically when the user modifies the 'location pull tank readings' field."""
        if not self.storage_location_id:
            return
        loc = self.storage_location_id
        if getattr(loc, 'is_storage_tank', False):
            if getattr(loc, 'base_temperature_f', None):
                self.temperature = loc.base_temperature_f
            if getattr(loc, 'storing_pressure', None):
                self.pressure = loc.storing_pressure
            if getattr(loc, 'storing_api_gravity', None):
                self.api_gravity = loc.storing_api_gravity

    def action_confirm(self):
        """Triggers the transition of the record to proceed with the 'confirm' step in the workflow."""
        res = super().action_confirm()

        picking = self.env['stock.picking'].search([
            ('origin', '=', _('Production - %s', self.task_id.display_name)),
            ('scheduled_date', '=', self.production_date),
            ('location_dest_id', '=', self.storage_location_id.id),
        ], order='id desc', limit=1)

        if picking:
            for move in picking.move_ids:
                line = self.line_ids.filtered(
                    lambda l: l.product_id == move.product_id
                )
                if line:
                    line = line[0]
                    move.write({
                        'hpm_temperature':   line.temperature,
                        'hpm_pressure':      line.pressure,
                        'hpm_api_gravity':   line.api_gravity,
                        'hpm_observed_qty':  line.observed_qty,
                        'hpm_vcf':           line.vcf,
                        'hpm_water_content': line.water_content,
                        'hpm_sulfur_content': line.sulfur_content,
                        'hpm_vcf_warnings':  line.vcf_warnings or '',
                    })
        return res


class ProductionWizardLine(models.TransientModel):
    """
    Per-line HPM measurement inputs.

    VCF and produced_qty computed via oil.hpm.calculation.engine.compute_vcf().
    vcf_warnings (new in v3) surfaces range validation messages inline
    in the wizard so the operator can see them before confirming.
    """
    _inherit = 'production.wizard.line'

    temperature = fields.Float(
        string='Temperature (°F)', digits=(6, 2), default=60.0, help="The temperature of the product measured during volume reading, in Fahrenheit.")
    pressure = fields.Float(
        string='Pressure (psi)', digits=(6, 2), default=0.0, help="The pressure of the product measured during volume reading, in psi.")
    api_gravity = fields.Float(
        string='API Gravity', digits=(5, 2), default=34.0, help="The API gravity of the petroleum product used to determine its standard quality and volume.")
    observed_qty = fields.Float(
        string='Observed Volume (raw)', digits=(12, 4), default=1.0, help="Specify the numerical measurement, volume, or financial amount for 'observed volume (raw)'.")
    water_content = fields.Float(
        string='Water / BSW (%)', digits=(6, 3), default=0.0, help="The percentage of basic sediment and water present in the liquid, used to calculate net volume.")
    sulfur_content = fields.Float(
        string='Sulfur (%)', digits=(6, 4), default=0.0, help="The mass percentage of sulfur present in the product, used for quality grading.")
    vcf = fields.Float(
        string='Correction Factor (VCF)', digits=(7, 5),
        compute='_compute_produced_qty', store=True, help="Specify the numerical measurement, volume, or financial amount for 'correction factor (vcf)'.")
    produced_qty = fields.Float(
        string='Produced Qty', required=True,
        compute='_compute_produced_qty', store=True, help="Specify the numerical measurement, volume, or financial amount for 'produced qty'.")
    vcf_warnings = fields.Text(
        string='VCF Warnings',
        compute='_compute_produced_qty', store=True,
        help="Range warnings from the last VCF computation for this line.",
    )
    is_hpm_enabled = fields.Boolean(
        compute='_compute_is_hpm_enabled', store=False, help="Enable or activate this option to apply 'is hpm enabled' status to the record.")

    @api.depends('product_id')
    def _compute_is_hpm_enabled(self):
        """Calculates and updates the 'hpm enabled' value automatically based on related operational inputs."""
        for line in self:
            if line.product_id:
                line.is_hpm_enabled = (
                    line.product_id.is_hpm_enabled
                    or (line.product_id.categ_id
                        and line.product_id.categ_id.is_hpm_enabled)
                )
            else:
                line.is_hpm_enabled = False

    @api.onchange('product_id')
    def _onchange_product_id_hpm(self):
        """Refreshes UI fields and updates default values dynamically when the user modifies the 'id hpm' field."""
        if not self.product_id:
            return
        if not self.observed_qty:
            self.observed_qty = 1.0
        self.is_hpm_enabled = (
            self.product_id.is_hpm_enabled
            or (self.product_id.categ_id
                and self.product_id.categ_id.is_hpm_enabled)
        )
        task = self.wizard_id.task_id
        self.temperature = (
            (task and getattr(task, 'current_temperature_f', None))
            or self.wizard_id.temperature
            or (self.product_id.is_hpm_enabled
                and self.product_id.hpm_standard_temperature)
            or (self.product_id.categ_id
                and self.product_id.categ_id.hpm_standard_temperature)
            or 60.0
        )
        self.pressure = (
            (task and getattr(task, 'current_pressure', None))
            or self.wizard_id.pressure
            or (self.product_id.is_hpm_enabled
                and self.product_id.hpm_standard_pressure)
            or (self.product_id.categ_id
                and self.product_id.categ_id.hpm_standard_pressure)
            or 0.0
        )
        self.api_gravity = (
            (task and getattr(task, 'current_api_gravity', None))
            or self.wizard_id.api_gravity
            or self.product_id.hpm_observed_api_gravity
            or (self.product_id.categ_id
                and self.product_id.categ_id.hpm_standard_api_gravity)
            or 34.0
        )
        if self.product_id.hpm_water_content:
            self.water_content = self.product_id.hpm_water_content
        if self.product_id.hpm_sulfur_content:
            self.sulfur_content = self.product_id.hpm_sulfur_content

    @api.depends(
        'observed_qty', 'temperature', 'pressure', 'api_gravity',
        'product_id', 'product_id.is_hpm_enabled',
        'product_id.categ_id.is_hpm_enabled',
        'product_id.hpm_standard_temperature',
        'product_id.hpm_standard_pressure',
        'product_id.hpm_standard_api_gravity',
        'product_id.hpm_standardisation',
        'product_id.hpm_api_product_group',
        'product_id.categ_id.hpm_api_product_group',
    )
    def _compute_produced_qty(self):
        """Calculates and updates the 'qty' value automatically based on related operational inputs."""
        engine = self.env['oil.hpm.calculation.engine']
        for line in self:
            vcf = 1.0
            standard_volume = line.observed_qty
            warnings_text = ''
            product = line.product_id
            hpm_on = product and (
                product.is_hpm_enabled
                or (product.categ_id and product.categ_id.is_hpm_enabled)
            )
            if hpm_on:
                config_source = (
                    product if product.is_hpm_enabled else product.categ_id
                )
                res = engine.compute_vcf(
                    config_source=config_source,
                    observed_temp=line.temperature,
                    observed_pressure=line.pressure,
                    observed_api_gravity=line.api_gravity,
                    observed_volume=line.observed_qty,
                )
                vcf = res['vcf']
                standard_volume = res['standard_volume']
                warnings = res.get('warnings', [])
                warnings_text = '\n'.join(warnings) if warnings else ''
            line.vcf = vcf
            line.produced_qty = standard_volume
            line.vcf_warnings = warnings_text
