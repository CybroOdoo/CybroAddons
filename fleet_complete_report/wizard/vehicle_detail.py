# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abhishek E T (odoo@cybrosys.com)
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
################################################################################

from odoo import api, fields, models


class VehicleDetail(models.TransientModel):
    _name = 'vehicle.detail'
    _description = 'Vehicle Details'

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
    def _onchange_date_from(self):
        """
        set valid start_date on changing it
        """
        if not self.end_date:
            if self.start_date and self.start_date > fields.Date.context_today(
                    self):
                self.start_date = fields.Date.context_today(self)
        else:
            if self.start_date and self.start_date > self.end_date:
                self.start_date = self.end_date

    @api.onchange('end_date')
    def _onchange_date_to(self):
        """
        set valid end_date on changing it
        """
        if self.start_date and self.end_date and \
                self.start_date > self.end_date:
            self.end_date = self.start_date
        if self.end_date and self.end_date > fields.Date.context_today(self):
            self.end_date = fields.Date.context_today(self)

    @api.onchange('state_ids')
    def _onchange_state_ids(self):
        """
        filter the vehicle_ids on changing the state_ids
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
