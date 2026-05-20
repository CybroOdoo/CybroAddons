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
#############################################################################

"""
stock.location extended with Storage Tank / ATG features.

When `is_storage_tank` is True the location behaves like a full Automatic
Tank Gauge (ATG) node:

  SCADA level sensor → stock.location.receive_level() → volume calculation
                                                       → stock.quant update
                                                       → high/low alarm HSE incident

Volume calculation:
  gross_volume_bbl = level_mm × bbl_per_mm
  temperature_correction = 1 - (expansion_coeff × (temp_f - base_temp_f))
  net_standard_volume = gross_volume_bbl × temperature_correction
  ullage = max_capacity_bbl - gross_volume_bbl
"""
from odoo import api, fields, models
from odoo.tools.translate import _

# Crude oil thermal expansion coefficient (per °F), ASTM D1250 approx.
DEFAULT_EXPANSION_COEFF = 0.00035


class OilTankType(models.Model):
    _name = 'oil.tank.type'
    _description = 'Oil Tank Type'
    name = fields.Char(string='Name', required=True)

class OilProductType(models.Model):
    _name = 'oil.product.type'
    _description = 'Oil Product Type'
    name = fields.Char(string='Name', required=True)


class StockLocation(models.Model):
    """
    Extends stock.location with Storage Tank (ATG) capabilities.
    All tank features are gated behind the `is_storage_tank` boolean.
    """
    _inherit = 'stock.location'

    # ── Storage Tank toggle ───────────────────────────────────────────────
    is_storage_tank = fields.Boolean(
        string='Is Storage Tank / ATG',
        default=False,
        tracking=True,
        help='When checked, this location behaves as an Automatic Tank Gauge '
             '(ATG) node with SCADA level/volume tracking and alarm management.',
    )

    # ── Tank Identity ─────────────────────────────────────────────────────
    tank_type_id = fields.Many2one(
        'oil.tank.type',
        string='Tank Type'
    )
    product_type_id = fields.Many2one(
        'oil.product.type',
        string='Product Type',
        tracking=True
    )
    tank_company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda s: s.env.company,
    )

    # ── SCADA tags linked to this location (via project) ─────────────────
    tank_scada_tag_ids = fields.Many2many(
        'scada.tag',
        compute='_compute_tank_scada_tags',
        string='SCADA Tags',
    )
    tank_scada_tag_count = fields.Integer(
        compute='_compute_tank_scada_tags',
        string='SCADA Tags',
    )

    # ── Tank Geometry ─────────────────────────────────────────────────────
    diameter_m = fields.Float(string='Diameter (m)', digits=(10, 3))
    shell_height_mm = fields.Float(string='Shell Height (mm)', digits=(12, 1))
    max_capacity_bbl = fields.Float(
        string='Max Capacity (bbl)',
        help='Maximum safe working volume in barrels.',
    )
    bbl_per_mm = fields.Float(
        string='Bbl per mm',
        digits=(10, 5),
        help='Tank strapping constant: barrels per mm of level.',
    )
    base_temperature_f = fields.Float(
        string='Base Temperature (°F)',
        default=60.0,
        help='Standard base temperature for volume correction (API = 60°F).',
    )
    expansion_coeff = fields.Float(
        string='Thermal Expansion Coeff (/°F)',
        default=DEFAULT_EXPANSION_COEFF,
        digits=(10, 6),
        help='Volumetric expansion coefficient per °F.',
    )

    # ── Live State (written by SCADA) ─────────────────────────────────────
    current_level_mm = fields.Float(
        string='Level (mm)',
        readonly=True,
        digits=(12, 1),
        help='Latest level reading from SCADA.',
    )
    current_temperature_f = fields.Float(
        string='Temperature (°F)',
        readonly=True,
        digits=(10, 2),
    )
    gross_volume_bbl = fields.Float(
        string='Gross Volume (bbl)',
        readonly=True,
        compute='_compute_volumes',
        store=True,
        digits=(16, 3),
    )
    net_standard_volume_bbl = fields.Float(
        string='Net Std Volume (bbl)',
        readonly=True,
        compute='_compute_volumes',
        store=True,
        digits=(16, 3),
        help='Volume corrected to base temperature (60°F).',
    )
    ullage_bbl = fields.Float(
        string='Ullage (bbl)',
        readonly=True,
        compute='_compute_volumes',
        store=True,
        digits=(16, 3),
        help='Available space = max capacity - gross volume.',
    )
    fill_percent = fields.Float(
        string='Fill %',
        readonly=True,
        compute='_compute_volumes',
        store=True,
        digits=(6, 2),
    )
    tank_state = fields.Selection([
        ('static',    'Static'),
        ('loading',   'Loading'),
        ('unloading', 'Unloading'),
        ('full',      'Full'),
    ], string='Tank Status', default='static', readonly=True, tracking=True)
    previous_level_mm = fields.Float(string='Previous Level (mm)', readonly=True)
    last_scada_sync = fields.Datetime(string='Last Level Sync', readonly=True)

    # ── Alarm Levels ──────────────────────────────────────────────────────
    high_high_level_mm = fields.Float(
        string='HH Level (mm)',
        help='High-High alarm — generate critical HSE incident.',
    )
    high_level_mm = fields.Float(
        string='High Level (mm)',
        help='High alarm — generate high-severity HSE incident.',
    )
    low_level_mm = fields.Float(
        string='Low Level (mm)',
        help='Low alarm — generate warning HSE incident.',
    )
    low_low_level_mm = fields.Float(
        string='LL Level (mm)',
        help='Low-Low alarm — generate critical HSE incident (pump damage risk).',
    )

    # ── Computed ──────────────────────────────────────────────────────────
    @api.depends('quant_ids.quantity', 'is_storage_tank', 'max_capacity_bbl',
                 'current_temperature_f', 'base_temperature_f', 'expansion_coeff')
    def _compute_volumes(self):
        """Calculate gross volume, net standard volume, ullage, and fill percentage from tank dimensions and SCADA readings."""
        for rec in self:
            # Gross volume is now sourced from on-hand stock at this location,
            # not from level_mm × bbl_per_mm. Each SCADA production reading
            # drops a validated picking into this location, so the quants are
            # always current.
            if rec.is_storage_tank:
                gross = sum(rec.quant_ids.mapped('quantity'))
            else:
                gross = 0.0

            temp_correction = 1.0
            if rec.current_temperature_f and rec.expansion_coeff:
                delta_t = rec.current_temperature_f - rec.base_temperature_f
                temp_correction = 1.0 - (rec.expansion_coeff * delta_t)
                temp_correction = max(0.95, min(1.05, temp_correction))  # clamp

            rec.gross_volume_bbl = gross
            rec.net_standard_volume_bbl = gross * temp_correction
            rec.ullage_bbl = max(0.0, (rec.max_capacity_bbl or 0.0) - gross)
            rec.fill_percent = (
                gross / rec.max_capacity_bbl * 100.0
            ) if rec.max_capacity_bbl else 0.0

    def _compute_tank_scada_tags(self):
        Tag = self.env['scada.tag']
        for rec in self:
            tags = Tag.search([
                ('odoo_model', '=', 'project.project'),
                ('project_id.storage_location_id', '=', rec.id),
            ])
            rec.tank_scada_tag_ids = tags
            rec.tank_scada_tag_count = len(tags)

    # ── SCADA Hook ────────────────────────────────────────────────────────
    def receive_level(self, level_mm, temperature_f=None, timestamp=None):
        """
        Called when Ignition pushes a new level reading for this storage location.
        Updates live state and evaluates alarm levels.

        :param float level_mm:      Raw level reading in mm.
        :param float temperature_f: Optional product temperature in °F.
        :param datetime timestamp:  Reading timestamp.
        """
        self.ensure_one()
        # Determine state
        new_state = 'static'
        if self.high_high_level_mm and level_mm >= self.high_high_level_mm:
            new_state = 'full'
        elif self.high_level_mm and level_mm >= self.high_level_mm:
            new_state = 'full'
        elif self.current_level_mm and level_mm > self.current_level_mm + 0.1:
            new_state = 'loading'
        elif self.current_level_mm and level_mm < self.current_level_mm - 0.1:
            new_state = 'unloading'

        vals = {
            'previous_level_mm': self.current_level_mm,
            'current_level_mm': level_mm,
            'tank_state': new_state,
            'last_scada_sync': timestamp or fields.Datetime.now(),
        }
        if temperature_f is not None:
            vals['current_temperature_f'] = temperature_f
        self.write(vals)
        self._evaluate_alarms(level_mm)

    def _evaluate_alarms(self, level_mm):
        """Check level against alarm setpoints and create HSE incidents as needed."""
        self.ensure_one()
        company_id = self.tank_company_id.id or self.env.company.id
        severity = None
        description = None

        if self.high_high_level_mm and level_mm >= self.high_high_level_mm:
            severity = 'critical'
            description = (
                f'Storage Location {self.display_name}: HIGH-HIGH level alarm — '
                f'{level_mm:.0f} mm ≥ {self.high_high_level_mm:.0f} mm HH setpoint.'
            )
        elif self.high_level_mm and level_mm >= self.high_level_mm:
            severity = 'high'
            description = (
                f'Storage Location {self.display_name}: HIGH level alarm — '
                f'{level_mm:.0f} mm ≥ {self.high_level_mm:.0f} mm H setpoint.'
            )
        elif self.low_low_level_mm and level_mm <= self.low_low_level_mm:
            severity = 'critical'
            description = (
                f'Storage Location {self.display_name}: LOW-LOW level alarm — '
                f'{level_mm:.0f} mm ≤ {self.low_low_level_mm:.0f} mm LL setpoint. '
                f'Risk of pump damage.'
            )
        elif self.low_level_mm and level_mm <= self.low_level_mm:
            severity = 'medium'
            description = (
                f'Storage Location {self.display_name}: LOW level alarm — '
                f'{level_mm:.0f} mm ≤ {self.low_level_mm:.0f} mm L setpoint.'
            )

        if severity:
            self.env['oil.hse.incident'].create({
                'incident_type': 'dangerous_occurrence',
                'severity': severity,
                'incident_date': fields.Datetime.now(),
                'immediate_action': description,
                'company_id': company_id,
            })

    # ── Smart Buttons ─────────────────────────────────────────────────────
    def action_view_scada_tags(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'SCADA Tags — {self.display_name}',
            'res_model': 'scada.tag',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.tank_scada_tag_ids.ids)],
        }

    def action_view_readings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Readings — {self.display_name}',
            'res_model': 'scada.reading',
            'view_mode': 'list,graph',
            'domain': [('tag_id', 'in', self.tank_scada_tag_ids.ids)],
        }

    def action_view_products(self):
        """List all stock quants currently held in this storage location."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Products in %s') % self.display_name,
            'res_model': 'stock.quant',
            'view_mode': 'list,form',
            'domain': [('location_id', '=', self.id)],
            'context': {
                'search_default_productgroup': 1,
                'default_location_id': self.id,
            },
        }
