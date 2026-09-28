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


class FlightAircraftClass(models.Model):
    """Manage aircraft classes."""
    _name = 'flight.aircraft.class'
    _description = 'Aircraft Class'
    _order = 'name'

    name = fields.Char(string='Class Name', required=True, help='Name of the aircraft class')
    code = fields.Char(string='Code', help='Unique code for the aircraft class')
    active = fields.Boolean(default=True, help='Set active to false to hide the aircraft class')

    _sql_name_unique = models.Constraint(
        'unique(name)',
        'An aircraft class with this name already exists.',
    )