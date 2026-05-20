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

from odoo import api, fields, models


MEASUREMENT_TYPES = (
    'pressure', 'temperature', 'flow_rate', 'level', 'gas_ppm',
    'vibration', 'valve_position', 'cumulative', 'other',
)


class ScadaReadingWizard(models.TransientModel):
    _name = 'scada.reading.wizard'
    _description = 'Simulate SCADA Reading'

    tag_id = fields.Many2one('scada.tag', string='Tag', required=True)
    quality = fields.Selection([
        ('good', 'Good'),
        ('bad', 'Bad'),
        ('uncertain', 'Uncertain'),
    ], string='Quality', default='good', required=True)
    timestamp = fields.Datetime(
        string='Timestamp', required=True,
        default=lambda self: fields.Datetime.now(),
    )

    # ── Measurement toggles mirrored from the tag (drive view visibility) ──
    measure_pressure = fields.Boolean(related='tag_id.measure_pressure')
    measure_temperature = fields.Boolean(related='tag_id.measure_temperature')
    measure_flow_rate = fields.Boolean(related='tag_id.measure_flow_rate')
    measure_level = fields.Boolean(related='tag_id.measure_level')
    measure_gas_ppm = fields.Boolean(related='tag_id.measure_gas_ppm')
    measure_vibration = fields.Boolean(related='tag_id.measure_vibration')
    measure_valve_position = fields.Boolean(related='tag_id.measure_valve_position')
    measure_cumulative = fields.Boolean(related='tag_id.measure_cumulative')
    measure_other = fields.Boolean(related='tag_id.measure_other')
    is_production_tag = fields.Boolean(related='tag_id.is_production_tag')

    # ── Per-measurement input values ───────────────────────────────────────
    val_pressure = fields.Float(string='Pressure')
    val_temperature = fields.Float(string='Temperature')
    val_flow_rate = fields.Float(string='Flow Rate')
    val_level = fields.Float(string='Level')
    val_gas_ppm = fields.Float(string='Gas (ppm)')
    val_vibration = fields.Float(string='Vibration')
    val_valve_position = fields.Float(string='Valve Position')
    val_cumulative = fields.Float(string='Cumulative')
    val_other = fields.Float(string='Other')

    # ── Production lines (one per product on the tag) ──────────────────────
    line_ids = fields.One2many(
        'scada.reading.wizard.line', 'wizard_id',
        string='Production Lines',
    )

    @api.onchange('tag_id')
    def _onchange_tag_id(self):
        """Pre-populate one production line per product registered on the tag."""
        if self.tag_id and self.tag_id.is_production_tag:
            self.line_ids = [(5, 0, 0)] + [
                (0, 0, {
                    'product_id': prod.id,
                    'scada_key': prod.scada_key or '',
                    'produced_qty': 0.0,
                })
                for prod in self.tag_id.product_ids
            ]
        else:
            self.line_ids = [(5, 0, 0)]

    def action_confirm(self):
        self.ensure_one()
        measurements = {
            mtype: getattr(self, f'val_{mtype}')
            for mtype in MEASUREMENT_TYPES
            if getattr(self.tag_id, f'measure_{mtype}')
        }
        production_data = {
            line.scada_key: line.produced_qty
            for line in self.line_ids
            if line.scada_key and line.produced_qty
        }
        self.tag_id.process_reading(
            measurements=measurements,
            quality=self.quality,
            timestamp=self.timestamp,
            production_data=production_data or None,
        )
        return {'type': 'ir.actions.act_window_close'}


class ScadaReadingWizardLine(models.TransientModel):
    _name = 'scada.reading.wizard.line'
    _description = 'Simulate SCADA Reading – Production Line'

    wizard_id = fields.Many2one(
        'scada.reading.wizard', required=True, ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
    )
    scada_key = fields.Char(
        string='SCADA Key',
        help='Identifier matched to product.scada_key when dispatching.',
    )
    produced_qty = fields.Float(string='Produced Qty', default=0.0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and self.product_id.scada_key:
            self.scada_key = self.product_id.scada_key
