# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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


class RepairTimesheet(models.Model):
    """This model is used to track timesheets for repair management."""
    _name = 'repair.timesheet'
    _description = "Repair Timesheet"
    _rec_name = 'user_id'

    inverse_id = fields.Many2one('machine.repair', string="Machine Repair",
                                 help="Reference to the related machine repair.")
    date = fields.Date(string='Date', help="Date of timesheet entry.")
    user_id = fields.Many2one('res.users', string="User",
                              help="User associated with this timesheet.")
    project_id = fields.Many2one('project.project', string="Project",
                                 help="Project linked to this timesheet.")
    description = fields.Char(string='Description',
                              help="Details of the work done.")
    hours = fields.Float(string='Duration', help="Total hours worked.")
    diagnosis_id = fields.Many2one('machine.diagnosis', string="Diagnosis",
                                   help="Related machine diagnosis.")
