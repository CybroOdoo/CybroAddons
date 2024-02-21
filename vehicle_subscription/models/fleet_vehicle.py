# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime
from odoo import api, fields, models


class FleetVehicle(models.Model):
    """Inherited model to add fields and functions"""
    _inherit = 'fleet.vehicle'

    free_km = fields.Float(string="Free KM", required=True, default=1500,
                           help="Set free km for each vehicle")
    subscription_price = fields.Float(string="Subscription price per day",
                                      help='Price of vehicle per day',
                                      required=True, default=12)
    states_id = fields.Many2one("res.country.state", string='State',
                                help="Help you choose the state")
    countries_id = fields.Many2one('res.country', string='Country',
                                   help="help you to choose country")
    insurance = fields.Char(string="Insurance",
                            help="Helps you to set Insurance")
    start = fields.Date(string="Start Date",
                        help="Helps you to choose start date")
    end = fields.Date(string="End Date", help="Helps you to choose end date")
    duration = fields.Integer(string="Duration", compute='_compute_duration')
    fuel = fields.Selection(selection=[('with_fuel', 'With Fuel'),
                                       ('without_fuel', 'Without Fuel')],
                            string="Fuel Choice", default='without_fuel',
                            help="Help you to choose the type of fuel")
    fuel_rate = fields.Integer(String="Rate", default=300, help="Rate of fuel")
    charge_km = fields.Integer(string="Charge in km", default=12,
                               help="Rate per kilometer")
    extra_km = fields.Float(string="Extra KMS", default=1500,
                            help="As per customer he/she can choose extra km")
    mileage = fields.Float(related='model_id.mileage', string='Mileage',
                           help="Helps to set mileage of vehicle")

    @api.depends('start', 'end')
    def _compute_duration(self):
        """Compute duration of days based on start and end date"""
        for record in self:
            if record.start and record.end:
                start = record.start.strftime("%Y-%m-%d")
                end = record.end.strftime("%Y-%m-%d")
                start_datetime = datetime.strptime(start, "%Y-%m-%d")
                end_datetime = datetime.strptime(end, "%Y-%m-%d")
                delta = end_datetime - start_datetime
                record.duration = delta.days
            else:
                record.duration = 0
