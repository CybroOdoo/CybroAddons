# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class FacilityRestaurant(models.Model):

    _inherit = "restaurant.floor"

    rest_floor_facility = fields.One2many('restaurant.floor.line', 'ref_field', string='Floor Facility')
    facility_service_percentage = fields.Float(compute='onchange_rest_facility', string="Active Facility Charge %")

    @api.multi
    @api.depends('rest_floor_facility')
    def onchange_rest_facility(self):
        for rec in self:
            sum_of_percentage = 0.0
            if rec.rest_floor_facility:
                for records in rec.rest_floor_facility:
                    sum_of_percentage += records.line_percentage
                rec.facility_service_percentage = sum_of_percentage


class FacilityRestaurantLines(models.Model):
    _name = "restaurant.floor.line"

    name = fields.Many2one('restaurant.floor.facility')
    line_percentage = fields.Float(string="Extra Charging Percentage")
    ref_field = fields.Many2one('restaurant.floor', invisible=True, ondelete='cascade')

    @api.onchange('name')
    def onchange_facility(self):
        if self.name:
            self.line_percentage = self.name.percentage


class FloorFacility(models.Model):

    _name = "restaurant.floor.facility"

    name = fields.Char(string="Name", required=True,)
    percentage = fields.Float(string="Extra Charging Percentage(%)", required=True,
                              help="Increment percentage of the each Product Price ")
    description = fields.Html(string="Description")
