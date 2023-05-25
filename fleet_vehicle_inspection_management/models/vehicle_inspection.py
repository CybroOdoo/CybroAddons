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
""" model for create vehicle inspections"""
from odoo import fields, models


class VehicleInspection(models.Model):
    """ add vehicle inspections """
    _name = 'vehicle.inspection'
    _description = 'Vehicle Inspection'

    name = fields.Char(string='Name', help='Name of vehicle inspection',
                       required=True)
    inspection_period = fields.Integer(string='Period(Days)',
                                       help='Recurring period of vehicle inspection')
    reminder_notification_days = fields.Integer(
        string='Reminder Notification(Days)',
        help='Number of days before want to send reminder email')
    user_id = fields.Many2one('res.users', string='Inspection Supervisor',
                              helps='Inspection supervisor')
    company_id = fields.Many2one('res.company', string='Company',
                                 help='Company Name')
