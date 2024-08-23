# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class EmployeeBiometric(models.TransientModel):
    """Transient model for Biometric device options in Employee"""
    _name = 'employee.biometric'
    _description = 'Employee Biometric Wizard'

    handle_create = fields.Selection(
        [('create_user', 'Create User')],
        'Handle Data', help='User Management', )
    handle_update_delete = fields.Selection(
        [('update_user', 'Update User'), ('delete_user', 'Delete User')],
        'Handle Data', help='User Management', )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', help='Select the Employee')
    is_biometric_user = fields.Boolean('Is Already User?',
                                       help='Checking if already a user?',
                                       compute='_compute_is_biometric_user')
    biometric_device_id = fields.Many2one('biometric.device.details',
                                          string='Biometric Device',
                                          help='Choose Biometric Device')

    @api.depends('employee_id')
    def _compute_is_biometric_user(self):
        """Compute if it is already a biometric user or not"""
        for record in self:
            if record.employee_id.device_id:
                record.is_biometric_user = True
            else:
                record.is_biometric_user = False

    def action_confirm_biometric_management(self):
        """Go to the desired functions in biometric.device.details"""
        if self.is_biometric_user:
            if self.handle_update_delete == 'update_user':
                self.employee_id.device_id.update_user(
                    employee_id=self.employee_id.id)
            else:
                self.employee_id.device_id.delete_user(
                    employee_id=self.employee_id.id,
                    delete_user_selection='device_only')
        else:
            self.employee_id.device_id = self.biometric_device_id.id
            self.biometric_device_id.set_user(employee_id=self.employee_id.id)
