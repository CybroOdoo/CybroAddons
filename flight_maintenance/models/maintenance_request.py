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
from odoo import api, fields, models


class MaintenanceRequest(models.Model):
    """Links aircraft maintenance requests to the flight module and keeps
    the aircraft's airworthiness status in sync with open grounding
    requests."""
    _inherit = 'maintenance.request'

    aircraft_id = fields.Many2one(
        'flight.aircraft',
        string='Aircraft',
        compute='_compute_aircraft_id',
        store=True,
        readonly=False,
        help='Aircraft this maintenance request applies to. Auto-linked from '
             'the selected Equipment when possible; can be overridden manually.',
    )
    grounding = fields.Boolean(
        string='Grounds Aircraft',
        default=True,
        help='While this request is open (its stage is not marked Done), the aircraft '
             'cannot be scheduled or dispatched.',
    )

    @api.depends('equipment_id')
    def _compute_aircraft_id(self):
        """Automatically link the aircraft when the selected equipment belongs
        to one. Runs server-side on create/write, so it works no matter which
        app the request is created from (Maintenance kanban, form, code...)."""
        for request in self:
            aircraft = request.aircraft_id
            if not aircraft and request.equipment_id:
                aircraft = self.env['flight.aircraft'].search(
                    [('equipment_id', '=', request.equipment_id.id)], limit=1,
                )
            elif aircraft and not request.equipment_id and aircraft.equipment_id:
                request.equipment_id = aircraft.equipment_id
            request.aircraft_id = aircraft

    @api.onchange('aircraft_id')
    def _onchange_aircraft_id_set_equipment(self):
        """Mirrors the link the other direction: picking an Aircraft first
        fills in its Equipment automatically."""
        if self.aircraft_id and self.aircraft_id.equipment_id and not self.equipment_id:
            self.equipment_id = self.aircraft_id.equipment_id.id

    def action_recompute_aircraft_link(self):
        """Manual fallback to (re)link this request's aircraft from its
        equipment. Mainly useful for requests created before this module's
        aircraft_id link existed, or where the link needs a manual nudge."""
        self._compute_aircraft_id()

    @api.model_create_multi
    def create(self, vals_list):
        """Updates aircraft maintenance status after creating requests and ensures
        aircraft_id and equipment_id are bi-directionally populated."""
        for vals in vals_list:
            if vals.get('aircraft_id') and not vals.get('equipment_id'):
                aircraft = self.env['flight.aircraft'].browse(vals['aircraft_id'])
                if aircraft.equipment_id:
                    vals['equipment_id'] = aircraft.equipment_id.id
            elif vals.get('equipment_id') and not vals.get('aircraft_id'):
                aircraft = self.env['flight.aircraft'].search(
                    [('equipment_id', '=', vals['equipment_id'])], limit=1,
                )
                if aircraft:
                    vals['aircraft_id'] = aircraft.id
        requests = super().create(vals_list)
        requests.mapped('aircraft_id')._recompute_maintenance_status()
        return requests

    def write(self, vals):
        """Updates aircraft maintenance status after modifying requests and ensures
        aircraft_id and equipment_id are bi-directionally populated."""
        if vals.get('aircraft_id') and 'equipment_id' not in vals:
            aircraft = self.env['flight.aircraft'].browse(vals['aircraft_id'])
            if aircraft.equipment_id:
                vals['equipment_id'] = aircraft.equipment_id.id
        elif vals.get('equipment_id') and 'aircraft_id' not in vals:
            aircraft = self.env['flight.aircraft'].search(
                [('equipment_id', '=', vals['equipment_id'])], limit=1,
            )
            if aircraft:
                vals['aircraft_id'] = aircraft.id
        aircraft_before = self.mapped('aircraft_id')
        result = super().write(vals)
        aircraft_after = self.mapped('aircraft_id')
        (aircraft_before | aircraft_after)._recompute_maintenance_status()
        return result

    def unlink(self):
        """Updates aircraft maintenance status after deleting requests."""
        aircraft = self.mapped('aircraft_id')
        result = super().unlink()
        aircraft._recompute_maintenance_status()
        return result
