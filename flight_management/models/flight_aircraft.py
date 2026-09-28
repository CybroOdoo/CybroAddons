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
from odoo.exceptions import ValidationError


class FlightAircraft(models.Model):
    """Manage aircraft records."""
    _name = 'flight.aircraft'
    _description = 'Aircraft'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Tail Number', required=True, tracking=True, help='Tail number or registration mark of the aircraft')
    code = fields.Char(string='Internal Code', copy=False, help='Unique internal identification code for the aircraft')
    model_id = fields.Many2one('flight.aircraft.model', string='Aircraft Model', required=True, ondelete='restrict', help='Model of the aircraft')
    make_id = fields.Many2one(
        'flight.aircraft.make', string='Manufacturer',
        related='model_id.make_id', store=True, readonly=True,
        help='Manufacturer of the aircraft',
    )
    class_id = fields.Many2one(
        'flight.aircraft.class', string='Class',
        related='model_id.class_id', store=True, readonly=True,
        help='Class category of the aircraft',
    )
    capacity = fields.Integer(string='Passenger Capacity', help='Maximum passenger seating capacity of the aircraft')
    home_base_id = fields.Many2one('flight.aerodrome', string='Home Base', help='Home base aerodrome for the aircraft')
    status = fields.Selection(
        [
            ('active', 'Active'),
            ('maintenance', 'In Maintenance'),
            ('grounded', 'Grounded'),
        ],
        string='Status', default='active', required=True, tracking=True,
        help='Current operational status of the aircraft',
    )
    active = fields.Boolean(default=True, help='Set active to false to hide the aircraft')

    @api.model_create_multi
    def create(self, vals_list):
        """Validate unique aircraft codes before creation."""
        for vals in vals_list:
            if vals.get('code'):
                existing = self.env['flight.aircraft'].search_count([('code', '=', vals['code'])])
                if existing:
                    raise ValidationError(
                        "An aircraft with internal code '%s' already exists." % vals['code']
                    )
        return super().create(vals_list)

    _sql_name_unique = models.Constraint(
        'unique(name)',
        'An aircraft with this tail number already exists.',
    )
    _sql_code_unique = models.Constraint(
        'unique(code)',
        'An aircraft with this internal code already exists.',
    )