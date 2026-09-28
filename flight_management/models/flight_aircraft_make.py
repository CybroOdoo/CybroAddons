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
from odoo import fields, models


class FlightAircraftMake(models.Model):
    """Manage aircraft manufacturers."""
    _name = 'flight.aircraft.make'
    _description = 'Aircraft Manufacturer'
    _order = 'name'

    name = fields.Char(string='Manufacturer', required=True, help='Name of the aircraft manufacturer')
    code = fields.Char(string='Code', help='Unique code for the aircraft manufacturer')
    active = fields.Boolean(default=True, help='Set active to false to hide the aircraft manufacturer')
    model_ids = fields.One2many('flight.aircraft.model', 'make_id', string='Models', help='Models associated with this manufacturer')

    _sql_name_unique = models.Constraint(
        'unique(name)',
        'A manufacturer with this name already exists.',
    )