# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class WorkTime(models.Model):
    """ This is used to assign the working time for employees """
    _name = 'working.time'
    _description = "Working Time"

    name = fields.Char(
        string='Shift Name', required=True,
        help='Descriptive title for this shift (e.g. Morning Shift).'
    )
    working_time = fields.Float(
        string='Standard Hours',
        help='Nominal standard working hours allocated per working day.'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        ondelete='restrict',
        help='Operating company associated with this work schedule.'
    )
    avg_working_hours = fields.Char(
        string='Average Working Hours',
        help='Average number of hours worked per week under this shift.'
    )
    working_hours = fields.One2many(
        'working.hours', 'working_id', string='Working Hours',
        help='Specific employee shift assignments linked with this schedule.'
    )


class WorkingHours(models.Model):
    """ Assigns the working hours """
    _name = 'working.hours'
    _description = "Working Hours"

    name = fields.Many2one(
        'hr.employee', domain="[('is_walker_sitters', '=', True)]",
        string='Employee', required=True, ondelete='cascade',
        help='Walker or sitter employee assigned to this shift slot.'
    )
    working_id = fields.Many2one(
        'working.time', string='Working Time Shift', ondelete='cascade',
        help='Parent working time shift profile.'
    )
    day = fields.Char(
        string='Day of Week',
        help='Day of the week for this shift (e.g. Monday, Tuesday).'
    )
    start_date = fields.Date(
        string='Start Date', required=True,
        help='Effective start date from which this work shift begins.'
    )
    end_date = fields.Date(
        string='End Date', required=True,
        help='Effective end date on which this work shift concludes.'
    )
