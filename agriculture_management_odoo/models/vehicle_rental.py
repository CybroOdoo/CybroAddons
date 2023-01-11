# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields, api


class VehicleRental(models.Model):
    _name = 'vehicle.rental'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Vehicle Rental'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('vehicle.details', string='Vehicle',
                                 required=True, tracking=True)
    no_of_days = fields.Float(string='No of Days', tracking=True,
                              compute='compute_days', store=True)
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    note = fields.Text(string='Description', tracking=True)

    @api.depends('start_date', 'end_date')
    def compute_days(self):
        if self.start_date and self.end_date:
            days = (self.end_date - self.start_date).days
            self.no_of_days = days
