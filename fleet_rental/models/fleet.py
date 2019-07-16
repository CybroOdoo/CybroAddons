# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2018-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AGPL (v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AGPL (AGPL v3) for more details.
#
##############################################################################

from odoo import models, fields


class FleetReservedTime(models.Model):
    _name = "rental.fleet.reserved"
    _description = "Reserved Time"

    customer_id = fields.Many2one('res.partner', string='Customer')
    date_from = fields.Date(string='Reserved Date From')
    date_to = fields.Date(string='Reserved Date To')
    reserved_obj = fields.Many2one('fleet.vehicle')


class EmployeeFleet(models.Model):
    _inherit = 'fleet.vehicle'

    rental_check_availability = fields.Boolean(default=True, copy=False)
    color = fields.Char(string='Color', default='#FFFFFF')
    rental_reserved_time = fields.One2many('rental.fleet.reserved', 'reserved_obj', String='Reserved Time', readonly=1,
                                           ondelete='cascade')
    fuel_type = fields.Selection([('gasoline', 'Gasoline'),
                                  ('diesel', 'Diesel'),
                                  ('electric', 'Electric'),
                                  ('hybrid', 'Hybrid'),
                                  ('petrol', 'Petrol')],
                                 'Fuel Type', help='Fuel Used by the vehicle')

    _sql_constraints = [('vin_sn_unique', 'unique (vin_sn)', "Chassis Number already exists !"),
                        ('license_plate_unique', 'unique (license_plate)', "License plate already exists !")]
