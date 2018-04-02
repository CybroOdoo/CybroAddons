# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Nilmar Shereef & Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import api, fields, models


class OHRMSConfiguration(models.TransientModel):
    _name = 'hr.config.settings'
    _inherit = 'res.config.settings'

    module_hr_custody = fields.Boolean(
        string='Manage the company properties when it is in the custody of an employee',
        help='Helps you to manage Custody Requests.\n'
             '- This installs the module Custody Management.')
    module_oh_employee_check_list = fields.Boolean(
        string="Manages employee's entry & exit Process",
        help='Helps you to manage Employee Checklist.\n'
             '- This installs the module Employee Checklist.')
    module_hr_employee_shift = fields.Boolean(
        string='Manage different type of shifts',
        help='Helps you to manage Employee Shift.\n'
             '- This installs the module Employee Shift.')
    module_hr_insurance = fields.Boolean(
        string='Manage Insurance for employees',
        help='Helps you to manage Employee Insurance.\n'
             '- This installs the module Employee Insurance.')
    module_oh_hr_lawsuit_management = fields.Boolean(
        string='Manage legal actions',
        help='Helps you to manage Lawsuit Management.\n'
             '- This installs the module Lawsuit Management.')
    module_hr_resignation = fields.Boolean(
        string='Handle the resignation process of the employee',
        help='Helps you to manage Resignation Process.\n'
             '- This installs the module Resignation Process.')
    module_hr_vacation_mngmt = fields.Boolean(
        string='Manage employee vacation',
        help='Helps you to manage Vacation Management.\n'
             '- This installs the module Vacation Management.')
    module_oh_hr_zk_attendance = fields.Boolean(
        string='Manage biometric device (Model: ZKteco uFace 202) integration with HR attendance (Face + Thumb)',
        help='Helps you to manage Biometric Device Integration.\n'
             '- This installs the module Biometric Device Integration.')

