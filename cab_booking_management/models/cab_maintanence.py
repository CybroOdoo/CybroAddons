# -*- coding: utf-8 -*-

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
        self.write({'fuel_used': total_fuel,
                    'odo_metre': odo_metres,
                    'cab_expense': expense,
                    'total_passenger': passenger})



