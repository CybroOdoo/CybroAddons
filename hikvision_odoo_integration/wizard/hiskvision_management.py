# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo.exceptions import UserError


class HikvisionManagement(models.TransientModel):
    """Wizard for managing Hikvision users."""

    _name = 'hikvision.management'
    _description = 'Hikvision User Management'

    manage_users = fields.Selection(
        [('create_user', 'Create User'),
         ('update_user', 'Update User'),
         ('delete_user', 'Delete User')],
        string='Action',
        help="Select the action to perform on Hikvision device users."
    )

    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        compute='_compute_employee_ids',
        help="List of employees filtered based on the selected action."
    )

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        domain="[('id', 'in', employee_ids)]",
        string='Employee',
        help="Employee on whom the selected Hikvision action will be performed."
    )

    device_id = fields.Many2one(
        comodel_name='hikvision.device',
        string='Device',
        required=True,
        help="Hikvision device on which the user management action will be executed."
    )

    @api.depends('manage_users')
    def _compute_employee_ids(self):
        """Compute employees based on selection."""
        for record in self:
            if record.manage_users == 'create_user':
                record.employee_ids = self.env['hr.employee'].search(
                    [('hikvision_number', '=', False)]).ids
            elif record.manage_users in ['delete_user', 'update_user']:
                record.employee_ids = self.env['hr.employee'].search(
                    [('hikvision_number', '!=', False)]).ids
            else:
                record.employee_ids = False

    def action_confirm_user_management(self):
        """Confirm user management action."""
        self.ensure_one()
        if not self.device_id:
            raise UserError(_("Please select a device."))

        if self.manage_users == 'create_user':
            self.device_id.create_hikvision_user(self.employee_id)
            message = _('User created successfully on Hikvision device.')
        elif self.manage_users == 'update_user':
            self.device_id.update_hikvision_user(self.employee_id)
            message = _('User updated successfully on Hikvision device.')
        else:
            self.device_id.delete_hikvision_user(self.employee_id)
            message = _('User deleted successfully on Hikvision device.')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}

            }
        }
