# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
from datetime import datetime


class VehicleDetail(models.Model):
    """ This model represents comprehensive details about vehicles within
     the context of agriculture management. It provides a structured way to
     store information related to various types of vehicles used for
     transportation and agricultural operations."""
    _name = 'vehicle.detail'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vehicle Details IN Agriculture Management"

    name = fields.Char(string='Name', tracking=True, readonly=True,
                       help="Mention the name of vehicle chose",
                       compute='_compute_vehicle_name')
    vehicle_main_id = fields.Many2one('fleet.vehicle',
                                      help="Select the vehicle that used for "
                                           "farming", string='Vehicle',
                                      required=True,
                                      tracking=True, domain=(
                                        [('state_id', '=', 'Registered')]))
    vehicle_type = fields.Selection(
        [('tractor', 'Tractor'), ('harvester', 'Harvester'),
         ('pickup', 'Pickup'), ('other', 'Other')],
        string='Vehicle Type', required=True,
        help=' Mention the status of vehicle ', tracking=True)
    vehicle_model = fields.Char(string='Model Year', store=True,
                                help='Mention the model of selected model',
                                compute='_compute_vehicle_model', tracking=True)
    note = fields.Text(string='Note', tracking=True,
                       help="Please describe any additional details here if "
                            "there is a need to mention additional data.")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='The company associated with the current user or '
        'environment.', default=lambda self: self.env.company)

    @api.depends("vehicle_main_id")
    def _compute_vehicle_name(self):
        """Function for auto update the name of vehicle based on model and
        brand"""
        for ref in self:
            ref.name = str(
                ref.vehicle_main_id.model_id.brand_id.name or " ") + "/" + str(
                ref.vehicle_main_id.model_id.name or " ") + "/" + str(
                ref.vehicle_main_id.license_plate or " ")

    @api.depends('vehicle_main_id')
    def _compute_vehicle_model(self):
        """ Function for selecting model of vehicle based on vehicle id"""
        for ref in self:
            ref.vehicle_model = False
            if ref.vehicle_main_id.registration_date:
                date = datetime.strptime(
                    str(ref.vehicle_main_id.registration_date), '%Y-%m-%d')
                ref.vehicle_model = str(date.year)
