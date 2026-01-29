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
from odoo import fields, models


class VehicleInspection(models.Model):
    """ Add vehicle inspections """
    _name = 'vehicle.inspection'
    _description = 'Vehicle Inspection'

    name = fields.Char(string='Name', help='Name of vehicle inspection',
                       required=True)
    inspection_period = fields.Integer(
        string='Period(Days)', help='Recurring period of vehicle inspection')
    reminder_notification_days = fields.Integer(
        string='Reminder Notification(Days)',
        help='Number of days before want to send reminder email')
    user_id = fields.Many2one('res.users', string='Inspection Supervisor',
                              helps='Inspection supervisor', required=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='Company Name')
