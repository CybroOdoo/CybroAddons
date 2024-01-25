# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class VehicleDetail(models.TransientModel):
    """
    Model for capturing and filtering vehicle details for report generation.
    """
    _name = 'vehicle.detail'
    _description = 'Vehicle Detail'

    vehicle_ids = fields.Many2many('fleet.vehicle', string='Vehicles',
                                   domain="[('state_id', 'in', state_ids)]",
                                   help="List of vehicles to generate report")
    state_ids = fields.Many2many(
        'fleet.vehicle.state', string='States', required=True,
        help='States of the vehicle')
    start_date = fields.Date(
        string='Start Date', required=True, default=fields.Date.context_today,
        help='Start date to filter the records')
    end_date = fields.Date(
        string='End Date', equired=True, default=fields.Date.context_today,
        help='End date to filter the records')
    exclude_vehicle_data = fields.Boolean(
        string='Exclude Vehicle Data', default=True,
        help='Enable this to hide the vehicle data in the report')

    @api.onchange('start_date')
    def _onchange_start_date(self):
        """
        Onchange method triggered when the start_date field is changed.

        This method ensures that the start_date is valid based on certain
        conditions.

        :return: None
        """
        if not self.end_date:
            if self.start_date and self.start_date > fields.Date.context_today(
                    self):
                self.start_date = fields.Date.context_today(self)
        else:
            if self.start_date and self.start_date > self.end_date:
                self.start_date = self.end_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        """
        Onchange method triggered when the end_date field is changed.

        This method ensures that the end_date is valid based on certain
        conditions.

        :return: None
        """
        if self.start_date and self.end_date and \
                self.start_date > self.end_date:
            self.end_date = self.start_date
        if self.end_date and self.end_date > fields.Date.context_today(self):
            self.end_date = fields.Date.context_today(self)

    @api.onchange('state_ids')
    def _onchange_state_ids(self):
        """
        Onchange method triggered when the state_ids field is changed.

        This method filters the vehicle_ids based on the selected state_ids.

        :return: None
        """
        if self.state_ids:
            self.vehicle_ids = self.vehicle_ids.filtered(
                lambda vehicle: vehicle.state_id.id in self.state_ids.ids)

    def action_print_report(self):
        """
        print PDF report for fleet based on selected data
        :return: report action
        """
        vehicles = self.vehicle_ids
        if not self.vehicle_ids:
            if self.state_ids:
                vehicles = self.env['fleet.vehicle'].search(
                    [('state_id', 'in', self.state_ids.ids)])
            else:
                vehicles = self.env['fleet.vehicle'].search([])
        data = {'vehicle_ids': vehicles.ids}
        return self.env.ref(
            'fleet_complete_report.action_report_vehicle_detail').report_action(
            self, data=data)
