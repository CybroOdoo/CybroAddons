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


class MaintenanceEquipmentScada(models.Model):
    """
    Extends maintenance.equipment (already extended by oil_erp_equipment)
    with SCADA integration fields.

    Live values (live_pressure / live_temperature / last_scada_sync) are
    computed on demand from scada.reading — the SCADA push pipeline only
    writes scada.reading rows, never mirror fields on the target record.
    """
    _inherit = 'maintenance.equipment'

    scada_tag_ids = fields.One2many(
        'scada.tag',
        'equipment_id',
        string='SCADA Tags',
        help='SCADA tags wired to this equipment.',
        readonly=True,
    )

    last_scada_sync = fields.Datetime(
        string='Last SCADA Sync',
        compute='_compute_live_scada_values',
        help='Timestamp of the most recent SCADA reading for this equipment.',
    )
    live_pressure = fields.Float(
        string='Live Pressure (PSI)',
        compute='_compute_live_scada_values',
        help='Latest pressure reading from any SCADA tag bound to this equipment.',
    )
    live_temperature = fields.Float(
        string='Live Temperature (°F)',
        compute='_compute_live_scada_values',
        help='Latest temperature reading from any SCADA tag bound to this equipment.',
    )

    @api.depends('scada_tag_ids')
    def _compute_live_scada_values(self):
        Reading = self.env['scada.reading']
        for rec in self:
            latest = Reading.search(
                [('equipment_id', '=', rec.id)],
                order='timestamp desc', limit=1,
            )
            rec.last_scada_sync = latest.timestamp or False

            temp = Reading.search([
                ('equipment_id', '=', rec.id),
                ('tag_id.measure_temperature', '=', True),
            ], order='timestamp desc', limit=1)
            rec.live_temperature = temp.val_temperature

            press = Reading.search([
                ('equipment_id', '=', rec.id),
                ('tag_id.measure_pressure', '=', True),
            ], order='timestamp desc', limit=1)
            rec.live_pressure = press.val_pressure

    def action_view_readings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Readings — {self.name}',
            'res_model': 'scada.reading',
            'view_mode': 'list,graph',
            'domain': [('equipment_id', '=', self.id)],
        }
