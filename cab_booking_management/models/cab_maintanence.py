# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#
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


class CabMaintanence(models.Model):
    _name = 'cab.maintanence'

    name = fields.Many2one('cab.management', string="Name", required=True)
    cab_log_date = fields.Date(string="Date", required=True)
    fuel_used = fields.Float(string="Fuel Used")
    odo_metre = fields.Float(string="OdoMetre Reading")
    cab_expense = fields.Float(string="Expense")
    total_passenger = fields.Integer(string="Total Passenger")

    @api.onchange('cab_log_date')
    def total_log_details(self):
        total_fuel = 0
        odo_metres = 0
        expense = 0
        passenger = 0
        for data in self.env['cab.log'].search([]):
            if data.cab_log_date == self.cab_log_date:
                total_fuel += data.fuel_used
                odo_metres += data.odo_metre
                expense += data.cab_expense
                passenger += data.total_passenger
        self.fuel_used = total_fuel
        self.odo_metre = odo_metres
        self.cab_expense = expense
        self.total_passenger = passenger



