# -*- coding: utf-8 -*-
#############################################################################
#
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
from odoo import api, fields, models, _


class FlightAircraft(models.Model):
    """Extends aircraft with maintenance integration and metrics."""
    _inherit = 'flight.aircraft'

    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Maintenance Equipment',
        readonly=True,
        copy=False,
        help='Auto-created and kept in sync with this aircraft; used as the asset '
             'referenced by maintenance requests.',
    )

    metric_ids = fields.One2many(
        'flight.aircraft.metric',
        'aircraft_id',
        string='Metric Entries',
        help='Metric log entries associated with this aircraft',
    )
    airframe_hours_total = fields.Float(
        string='Airframe Hours',
        compute='_compute_metric_totals',
        store=True,
        help='Total accumulated airframe operational hours',
    )
    engine_hours_total = fields.Float(
        string='Engine Hours',
        compute='_compute_metric_totals',
        store=True,
        help='Total accumulated engine operational hours',
    )
    cycles_total = fields.Float(
        string='Cycles',
        compute='_compute_metric_totals',
        store=True,
        help='Total accumulated flight cycles',
    )
    fuel_used_total = fields.Float(
        string='Fuel Used (gal)',
        compute='_compute_metric_totals',
        store=True,
        help='Total fuel consumed in gallons',
    )

    maintenance_request_ids = fields.One2many(
        'maintenance.request',
        'aircraft_id',
        string='Maintenance Requests',
        help='Maintenance requests linked to this aircraft',
    )
    maintenance_request_count = fields.Integer(
        string='Maintenance Request Count',
        compute='_compute_maintenance_request_count',
        help='Number of maintenance requests linked to this aircraft',
    )

    @api.depends('metric_ids.metric_type', 'metric_ids.value')
    def _compute_metric_totals(self):
        """Computes the total values for each aircraft metric."""
        for aircraft in self:
            airframe = engine = cycles = fuel = 0.0
            for metric in aircraft.metric_ids:
                if metric.metric_type == 'airframe_hours':
                    airframe += metric.value
                elif metric.metric_type == 'engine_hours':
                    engine += metric.value
                elif metric.metric_type == 'cycles':
                    cycles += metric.value
                elif metric.metric_type == 'fuel_used':
                    fuel += metric.value
            aircraft.airframe_hours_total = airframe
            aircraft.engine_hours_total = engine
            aircraft.cycles_total = cycles
            aircraft.fuel_used_total = fuel

    @api.depends('maintenance_request_ids')
    def _compute_maintenance_request_count(self):
        """Computes the number of maintenance requests for each aircraft."""
        for aircraft in self:
            aircraft.maintenance_request_count = len(aircraft.maintenance_request_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Create aircraft records and sync linked maintenance equipment."""
        aircraft_recs = super().create(vals_list)
        aircraft_recs._sync_maintenance_equipment()
        return aircraft_recs

    def write(self, vals):
        """Update aircraft records and sync linked maintenance equipment on name or model change."""
        result = super().write(vals)
        if 'name' in vals or 'model_id' in vals:
            self._sync_maintenance_equipment()
        return result

    def _sync_maintenance_equipment(self):
        """Create or update linked maintenance equipment record for each aircraft."""
        equipment_model = self.env['maintenance.equipment']
        category = self.env.ref(
            'flight_maintenance.equipment_category_aircraft', raise_if_not_found=False,
        )
        for aircraft in self:
            equipment_name = (
                f"{aircraft.name} ({aircraft.model_id.display_name})"
                if aircraft.model_id else aircraft.name
            )
            if aircraft.equipment_id:
                aircraft.equipment_id.write({'name': equipment_name})
            else:
                equipment = equipment_model.create({
                    'name': equipment_name,
                    'category_id': category.id if category else False,
                })
                aircraft.equipment_id = equipment.id

    def action_view_maintenance_requests(self):
        """Return action to open maintenance requests linked to this aircraft."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Maintenance Requests'),
            'res_model': 'maintenance.request',
            'view_mode': 'list,form,kanban',
            'domain': [('aircraft_id', '=', self.id)],
            'context': {
                'default_aircraft_id': self.id,
                'default_equipment_id': self.equipment_id.id,
                'default_grounding': True,
            },
        }

    def _recompute_maintenance_status(self):
        """Aircraft status is 'maintenance' iff at least one grounding request
        is currently open (its stage is not marked Done). 'grounded' is treated
        as a manual/permanent status and is never overridden here."""
        for aircraft in self:
            if aircraft.status == 'grounded':
                continue
            open_grounding = self.env['maintenance.request'].search_count([
                ('aircraft_id', '=', aircraft.id),
                ('grounding', '=', True),
                ('stage_id.done', '=', False),
            ])
            if open_grounding and aircraft.status != 'maintenance':
                aircraft.status = 'maintenance'
            elif not open_grounding and aircraft.status == 'maintenance':
                aircraft.status = 'active'
