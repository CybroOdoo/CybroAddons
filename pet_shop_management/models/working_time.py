"""Working shifts"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
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
from odoo import fields, models


class WorkTime(models.Model):
    """This is used assign the working time for employee"""
    _name = 'working.time'
    _description = "working time"

    working_time = fields.Float(string='Working Time',
                                help='Working time of employee')
    company_id = fields.Many2one('res.company', string='Company',
                                 help='Company')
    name = fields.Char(string='Name', help='Name of shift')
    avg_working_hours = fields.Char(string='Average Working Hours',
                                    help='Average working hours')
    working_hours = fields.One2many('working.hours',
                                    'working_id',
                                    string='Working hours',
                                    help='working hours')


class WorkingHours(models.Model):
    """Assigns the working hours"""
    _name = 'working.hours'
    _description = "working hours"

    name = fields.Many2one('hr.employee',
                           domain="[('is_walker_sitters', '=', True)]",
                           string='Name', help='Name of the employee')
    working_id = fields.Many2one('working.time', string='Working time',
                                 help='Working time of the employee')
    day = fields.Char(string='Day of Week', help='Day of the week')
    start_date = fields.Date(string='Start Date',
                             help='Start date of the shift')
    end_date = fields.Date(string='End Date', help='Start date of the shift')
