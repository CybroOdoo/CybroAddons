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
from odoo import models, _


class FlightFlight(models.Model):
    """Extends flight completion to record aircraft metrics."""
    _inherit = 'flight.flight'

    def action_complete(self):
        """Creates aircraft metric entries after completing a flight."""
        result = super().action_complete()
        for flight in self:
            if not flight.aircraft_id or not flight.actual_departure or not flight.actual_arrival:
                continue
            duration_hours = (flight.actual_arrival - flight.actual_departure).total_seconds() / 3600.0
            if duration_hours <= 0:
                continue
            notes = _('Auto-logged from %s', flight.display_name or flight.name or '')
            self.env['flight.aircraft.metric'].create([
                {
                    'aircraft_id': flight.aircraft_id.id,
                    'metric_type': 'airframe_hours',
                    'value': duration_hours,
                    'flight_id': flight.id,
                    'notes': notes,
                },
                {
                    'aircraft_id': flight.aircraft_id.id,
                    'metric_type': 'cycles',
                    'value': 1,
                    'flight_id': flight.id,
                    'notes': notes,
                },
            ])
        return result
