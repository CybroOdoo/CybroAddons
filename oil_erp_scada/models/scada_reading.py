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

from odoo import fields, models


class ScadaReading(models.Model):
    """
    Append-only time-series log of every sensor reading received from SCADA.
    One row per data point — never updated, only created.

    Retention policy: configure an ir.cron to call
    ScadaReading.purge_old_readings() periodically.
    """
    _name = 'scada.reading'
    _description = 'SCADA Sensor Reading'
    _order = 'timestamp desc, id desc'
    _log_access = False  # no create_uid / write_uid — pure timeseries

    tag_id = fields.Many2one(
        'scada.tag',
        string='Tag',
        required=True,
        ondelete='cascade',
        index=True,
    )
    # Denormalised for fast queries without joining scada.tag each time
    tag_path = fields.Char(
        related='tag_id.tag_path',
        store=True,
        string='Tag Path',
        index=True,
    )

    equipment_id = fields.Many2one(
        related='tag_id.equipment_id',
        store=True,
        string='Equipment',
        index=True,
    )
    project_id = fields.Many2one(related='tag_id.project_id', store=True, string='Project', index=True)
    storage_location_id = fields.Many2one(related='tag_id.project_id.storage_location_id', store=True, string='Storage Location', index=True)

    well_id = fields.Many2one(related='tag_id.well_id', store=True, string='Well', index=True)
    carrier_id = fields.Many2one(related='tag_id.carrier_id', store=True, string='Pipeline Method', index=True)

    # ── Measurement ────────────────────────────────────────────────────────
    val_pressure = fields.Float(string='Pressure', digits=(16, 4))
    val_temperature = fields.Float(string='Temperature', digits=(16, 4))
    val_flow_rate = fields.Float(string='Flow Rate', digits=(16, 4))
    val_level = fields.Float(string='Level', digits=(16, 4))
    val_gas_ppm = fields.Float(string='Gas Concentration (ppm)', digits=(16, 4))
    val_vibration = fields.Float(string='Vibration', digits=(16, 4))
    val_valve_position = fields.Float(string='Valve Position', digits=(16, 4))
    val_cumulative = fields.Float(string='Cumulative Volume (meter)', digits=(16, 4))
    val_other = fields.Float(string='Other', digits=(16, 4))
    quality = fields.Selection(
        [('good', 'Good'), ('bad', 'Bad'), ('uncertain', 'Uncertain')],
        string='OPC-UA Quality',
        default='good',
        required=True,
    )
    timestamp = fields.Datetime(
        string='Timestamp',
        required=True,
        index=True,
        default=fields.Datetime.now,
    )
    source = fields.Selection(
        [
            ('ignition', 'Ignition SCADA'),
            ('manual', 'Manual Entry'),
            ('api', 'External API'),
        ],
        string='Source',
        default='ignition',
        required=True,
    )
    company_id = fields.Many2one(
        related='tag_id.company_id',
        store=True,
        string='Company',
    )

    production_line_ids = fields.One2many(
        'scada.reading.product',
        'reading_id',
        string='Production Quantities'
    )

    # ── Maintenance ────────────────────────────────────────────────────────
    def purge_old_readings(self, days=90):
        """
        Delete readings older than `days`.  Called from ir.cron.
        Override days in cron code field: self.env['scada.reading'].purge_old_readings(180)
        """
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=days)
        old = self.search([('timestamp', '<', cutoff)])
        count = len(old)
        old.unlink()
        return count

    def action_do_nothing(self):
        """Dummy method to prevent opening the form view when clicking a row."""
        return True
