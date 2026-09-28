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


class FlightAircraftModel(models.Model):
    """Manage aircraft models."""
    _name = 'flight.aircraft.model'
    _description = 'Aircraft Model'
    _order = 'name'

    name = fields.Char(string='Model Name', required=True, help='Name of the aircraft model')
    code = fields.Char(string='Code', help='Unique code for the aircraft model')
    make_id = fields.Many2one('flight.aircraft.make', string='Manufacturer', required=True, ondelete='restrict', help='Manufacturer of this aircraft model')
    class_id = fields.Many2one('flight.aircraft.class', string='Class', ondelete='restrict', help='Class category of this aircraft model')
    default_capacity = fields.Integer(string='Default Capacity', help='Default passenger seating capacity for this aircraft model')
    active = fields.Boolean(default=True, help='Set active to false to hide the aircraft model')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True, help='Display name combining manufacturer and model name')

    @api.depends('name', 'make_id.name')
    def _compute_display_name(self):
        """Compute the aircraft model display name."""
        for model in self:
            model.display_name = f"{model.make_id.name} {model.name}" if model.make_id else model.name

    _sql_name_make_unique = models.Constraint(
        'unique(name, make_id)',
        'This model already exists for the selected manufacturer.',
    )