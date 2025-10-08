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
from odoo import api, fields, models, _


class ZkUserManagement(models.TransientModel):
    """Wizard for managing Employee data In Biometric Device """
    _name = 'zk.user.management'
    _description = 'ZK User Management Wizard'

    manage_users = fields.Selection(
        [('get_users', 'Get all Users'), ('create_user', 'Create User'),
         ('update_user', 'Update User'),
         ('delete_user', 'Delete User')],
        'Manage Users', help='User Management', required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees',
                                    compute='_compute_employee_ids')
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', help='Select the Employee',
        domain="[('id', 'in', employee_ids)]")
    delete_user_selection = fields.Selection(
        [('device_only', 'From Device Only'),
         ('both_device', 'From Both Device and Odoo')], string='Delete From',
        default='device_only', help='Choose the delete option')

    @api.depends('manage_users')
    def _compute_employee_ids(self):
        """Compute Employees By the Selected Option"""
        for record in self:
            if record.manage_users == 'create_user':
                record.employee_ids = self.env['hr.employee'].search(
                    [('device_id', '!=',
                      int(self.env.context.get('active_id')))]).ids
            elif record.manage_users in ['delete_user', 'update_user']:
                record.employee_ids = self.env['hr.employee'].search(
                    [('device_id', '=',
                      int(self.env.context.get('active_id')))]).ids
            else:
                record.employee_ids = False

    def action_confirm_user_management(self):
        """Function to works according to the selected option"""
        if self.manage_users:
            if self.manage_users == 'get_users':
                self.env['biometric.device.details'].browse(
                    int(self.env.context.get('active_id'))).get_all_users()
                return {
                    'name': _("ZK Users"),
                    'type': 'ir.actions.act_window',
                    'res_model': 'hr.employee',
                    'context': {'create': False},
                    'view_mode': 'tree,form',
                    'domain': [('device_id', '=',
                                int(self.env.context.get('active_id')))]
                }
            elif self.manage_users == 'create_user':
                self.env['biometric.device.details'].browse(
                    int(self.env.context.get('active_id'))).set_user(
                    employee_id=self.employee_id.id)
            elif self.manage_users == 'update_user':
                self.env['biometric.device.details'].browse(
                    int(self.env.context.get('active_id'))).update_user(
                    employee_id=self.employee_id.id)
            else:
                self.env['biometric.device.details'].browse(
                    int(self.env.context.get('active_id'))).delete_user(
                    employee_id=self.employee_id.id,
                    delete_user_selection=self.delete_user_selection)
