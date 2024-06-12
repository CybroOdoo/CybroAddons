# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class EmployeeDetails(models.Model):
    """Creating new model for inputting employee information
     such as names and shifts."""
    _name = "employee.details"
    _description = "Employee Details"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'employee_name_id'

    employee_name_id = fields.Many2one('hr.employee',
                                       string='Employee Name',
                                       help="Choose Employee Name",
                                       required=True)
    time_shift_id = fields.Many2one('cleaning.shift',
                                    string='Time Shift',
                                    help="Choose Time Shift for Employee",
                                    required=True)
