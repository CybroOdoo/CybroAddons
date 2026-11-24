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
from odoo.exceptions import ValidationError


class FlightAircraftMetric(models.Model):
    """Manages aircraft metric entries."""
    _name = 'flight.aircraft.metric'
    _description = 'Aircraft Metric Entry'
    _order = 'date desc'

    aircraft_id = fields.Many2one(
        'flight.aircraft',
        string='Aircraft',
        required=True,
        ondelete='cascade',
        help='Aircraft associated with this metric entry',
    )
    metric_type = fields.Selection(
        [
            ('airframe_hours', 'Airframe Hours'),
            ('engine_hours', 'Engine Hours'),
            ('cycles', 'Cycles'),
            ('fuel_used', 'Fuel Used (gal)'),
        ],
        string='Metric',
        required=True,
        help='Type of metric being recorded',
    )
    value = fields.Float(
        string='Value',
        required=True,
        help='Incremental value added by this entry.',
    )
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        required=True,
        help='Date and time when the metric was logged',
    )
    flight_id = fields.Many2one(
        'flight.flight',
        string='Source Flight',
        readonly=True,
        help='Automatically set when this entry was generated from a completed flight.',
    )
    notes = fields.Char(
        string='Notes',
        help='Additional comments or details about the metric entry',
    )

    @api.constrains('value')
    def _check_value(self):
        """Validates that the metric value is not negative."""
        for metric in self:
            if metric.value < 0:
                raise ValidationError(_("Metric value cannot be negative."))
