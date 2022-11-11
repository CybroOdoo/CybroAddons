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
from datetime import datetime
from odoo import models, fields, api


class VehicleDetails(models.Model):
    _name = 'vehicle.details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vehicle Details"

    name = fields.Char(string='Name', tracking=True, )
    vehicle_main_id = fields.Many2one('fleet.vehicle', string='Vehicle',
                                      required=True, tracking=True,
                                      domain=(
                                          [('state_id', '=', 'Registered')]))
    vehicle_type = fields.Selection(
        [('tractor', 'Tractor'), ('harvester', 'Harvester'),
         ('pickup', 'Pickup'), ('other', 'Other')],
        string='Vehicle Type', required=True, tracking=True)
    vehicle_model = fields.Char(string='Model Year', compute='compute_model',
                                store=True, tracking=True)
    note = fields.Text(string='Note', tracking=True)

    @api.onchange("vehicle_main_id")
    def onchange_vehicle(self):
        self.name = str(
            self.vehicle_main_id.model_id.brand_id.name or " ") + "/" + str(
            self.vehicle_main_id.model_id.name or " ") + "/" + str(
            self.vehicle_main_id.license_plate or " ")

    @api.depends('vehicle_main_id')
    def compute_model(self):
        for ref in self:
            ref.vehicle_model = False
            if ref.vehicle_main_id.registration_date:
                date = datetime.strptime(
                    str(ref.vehicle_main_id.registration_date), '%Y-%m-%d')
                ref.vehicle_model = str(date.year)
