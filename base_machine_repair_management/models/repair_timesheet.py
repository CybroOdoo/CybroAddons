# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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
    """This is used for thr timesheet of repair management"""
    _name = 'repair.timesheet'
    _description = "Timesheet Of The Repair"
    _rec_name = 'user_id'

    inverse_id = fields.Many2one('machine.repair', string="Machine Repair",
                                 help="Inverse field of the models "
                                      "'machine.repair'")
    date = fields.Date(string='Date', help="Time sheet creation date")
    user_id = fields.Many2one('res.users', string="User",
                              help="Time sheet for the user")
    project_id = fields.Many2one('project.project', string="Project",
                                 help="Project for the user")
    description = fields.Char(string='Description',
                              help="Description for the user's timesheet")
    hours = fields.Float(string='Duration', help="Duration of the Work")
    diagnosis_id = fields.Many2one('machine.diagnosis',
                                   string="Diagnosis",
                                   help="Machine diagnosis")
