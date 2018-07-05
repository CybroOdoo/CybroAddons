# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class CabManagement(models.Model):
    _name = 'cab.management'

    name = fields.Char(compute="complete_name_compute", string="Cab Name")
    ref_name = fields.Char(string="Cab Name", required=True)
    cab_image = fields.Binary(string='Image', store=True, attachment=True)
    licence_plate = fields.Char(string="Licence Plate", required=True)
    activity_period_from = fields.Date(string="Activity Period")
    activity_period_to = fields.Date(string="To")
    driver_plot = fields.Char(string="Driver Ploted")
    cab_value = fields.Float(string="Cab Value")
    cab_model = fields.Char(string="Cab Model")
    cab_color = fields.Char(string="Cab Color")
    aq_date = fields.Date(string="Aquisition Date")
    chas_no = fields.Char(string="Chasis No")
    odo_reading = fields.Float(string="Odometre Reading")
    seating_capacity = fields.Integer(string="Seating Capacity", required=True)
    fuel_type = fields.Char(string="Fuel Type")
    related_log_details = fields.One2many('cab.log', string="Log Details", compute="auto_fetch_log_details")
    total_log_details = fields.One2many('cab.maintanence', string='Total Expenses', compute="auto_fetch_total_details")
    location_log_details = fields.One2many('cab.log', string="Location", compute="auto_fetch_location_details")

    @api.onchange('licence_plate')
    def check_unique_constraint(self):
        for records in self.env['cab.management'].search([]):
            if self.licence_plate == records.licence_plate:
                raise ValidationError("Record already exists and violates unique field constraint")

    @api.one
    def complete_name_compute(self):
        self.name = self.ref_name
        if self.licence_plate:
            self.name = str(self.licence_plate) + ' / ' + str(self.ref_name)

    @api.onchange('activity_period_from', 'activity_period_to')
    def auto_fetch_log_details(self):
        if self.activity_period_from and self.activity_period_to:
            if self.activity_period_from <= self.activity_period_to:
                data = self.env['cab.log'].search([("cab_log_date", ">=", self.activity_period_from),
                                                   ("cab_log_date", "<=", self.activity_period_to)])
                self.related_log_details = data
            else:
                self.activity_period_to = 0
                raise UserError("Enter Valid Dates")

    @api.onchange('activity_period_from', 'activity_period_to')
    def auto_fetch_total_details(self):
        if self.activity_period_from and self.activity_period_to:
            if self.activity_period_from <= self.activity_period_to:
                data = self.env['cab.maintanence'].search([("cab_log_date", ">=", self.activity_period_from),
                                                           ("cab_log_date", "<=", self.activity_period_to)])
                self.total_log_details = data
            else:
                raise UserError("Enter Valid Dates")

    @api.onchange('activity_period_from', 'activity_period_to')
    def auto_fetch_location_details(self):
        if self.activity_period_from and self.activity_period_to:
            if self.activity_period_from <= self.activity_period_to:
                data = self.env['cab.log'].search([("cab_log_date", ">=", self.activity_period_from),
                                                   ("cab_log_date", "<=", self.activity_period_to)])
                self.location_log_details = data
            else:
                raise UserError("Enter Valid Dates")

