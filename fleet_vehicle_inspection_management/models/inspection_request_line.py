# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
#    Version 3 (AGPL v3)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
""" model for vehicle inspection lines"""
from odoo import fields, models


class InspectionRequestLine(models.Model):
    """ add inspection requests """
    _name = 'inspection.request.line'
    _description = 'Inspection Request Line'

    fleet_vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle',
                                       help='Select vehicle for the inspection request.')
    description = fields.Char(string='Description',
                              help='Description for inspection request')
    inspection_id = fields.Many2one('vehicle.inspection', required=True,
                                    help='Select vehicle inspection',
                                    string='Inspection Reference')
    inspection_period = fields.Integer(string='Period(Days)',
                                       related='inspection_id.inspection_period',
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
    inspection_request_reference = fields.Integer(
        string='Inspection Request Reference',
        help='Inspection Request Reference')
