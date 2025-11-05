# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date


class CabBooking(models.Model):
    _name = 'cab.booking'
    _rec_name = 'booking_date'

    booking_date = fields.Date(string="Booking Date", default=date.today(), required=True)
    cab_timing = fields.Many2one('cab.time', string="Timing", required=True)
    cab_routes = fields.Many2one('cab.location', string="Route From", required=True)
    cab_routes_to = fields.Many2one('cab.location', string="Route To", required=True)
    seat_available = fields.One2many('cab.timing', compute="scheduled_details")

    @api.onchange('cab_routes', 'cab_timing', 'cab_routes_to')
    def scheduled_details(self):
        data = self.env['cab.timing'].search([('cab_route.name', '=', self.cab_routes.name),
                                              ('cab_time.name', '=', self.cab_timing.name),
                                              ('cab_route_to.name', '=', self.cab_routes_to.name)])
        self.seat_available = data










