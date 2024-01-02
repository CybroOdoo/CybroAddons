# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
###############################################################################
""" model for vehicle inspection lines"""
from odoo import fields, models


class InspectionRequestLine(models.Model):
    """ add inspection requests """
    _name = 'inspection.request.line'
    _description = 'Inspection Request Line'
    _rec_name = 'fleet_vehicle_id'

    fleet_vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle',
        help='Select vehicle for the inspection request.')
    description = fields.Char(string='Description',
                              help='Description for inspection request')
    inspection_id = fields.Many2one('vehicle.inspection', required=True,
                                    help='Select vehicle inspection',
                                    string='Inspection Reference')
    inspection_period = fields.Integer(
        string='Period(Days)', related='inspection_id.inspection_period',
        help='Recurring interval of vehicle inspection')
    reminder_notification = fields.Integer(
        string='Reminder Notification Date',
        related='inspection_id.reminder_notification_days',
        help='Number of days before need to send Reminder Email')
    user_id = fields.Many2one('res.users', string='Inspection Supervisor',
                              related='inspection_id.user_id',
                              help='Instruction Supervisor')
    last_inspection_date = fields.Date(string='Last Inspection Date',
                                       help='Date of last inspection ')
    next_inspection_date = fields.Date(string='Next Inspection Date',
                                       help='Date of next inspection')
    inspection_request_reference_id = fields.Many2one(
        'inspection.request.line', string='Inspection Request Reference',
        help='Inspection Request Reference')
