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
from odoo import api, fields, models


class UserAudit(models.Model):
    """We can manage user audit configuration.We can add user
                model etc. which are to track"""
    _name = "user.audit"
    _description = "User Audit Log Configuration"

    name = fields.Char(required=True, string="Name", help="Name of the log")
    is_read = fields.Boolean(string="Read",
                             help="Enabling we can track all read activities "
                                  "It will track all your read activity that "
                                  "may increase the size of the log that may "
                                  "cause some problem with your data base")
    is_write = fields.Boolean(string="Write",
                              help="Enabling we can track all write "
                                   "activities")
    is_create = fields.Boolean(string="Create",
                               help="Enabling we can track all create "
                                    "activities")
    is_delete = fields.Boolean(string="Delete",
                               help="Enabling we can track all delete "
                                    "activities")
    is_all_users = fields.Boolean(string="All Users",
                                  help="Enabling we can track activities of "
                                       "all users")
    user_ids = fields.Many2many('res.users', string="Users",
                                help="Manage users")
    model_ids = fields.Many2many('ir.model', string="Model",
                                 help='Used to select which model is to track')

    def _is_user_tracked(self, audit):
        """Check if current user should be tracked by this audit configuration.

        Args:
            audit: user.audit recordset

        Returns:
            bool: True if current user should be tracked
        """
        return audit.is_all_users or self.env.uid in audit.user_ids.ids

    def _is_operation_tracked(self, operation_type, audit):
        """Check if the operation type is enabled for tracking.

        Args:
            operation_type: str - 'create', 'read', 'write', or 'delete'
            audit: user.audit recordset

        Returns:
            bool: True if operation should be tracked
        """
        operation_map = {
            'create': audit.is_create,
            'read': audit.is_read,
            'write': audit.is_write,
            'delete': audit.is_delete,
        }
        return operation_map.get(operation_type, False)

    @api.model
    def create_audit_log(self, res_model, res_id=False, operation_type='create'):
        """Create audit log entries based on configuration.

        Args:
            res_model: str - Model name (e.g., 'res.partner')
            res_id: int or list - Record ID(s)
            operation_type: str - Operation type: 'create', 'read', 'write', 'delete'
        """
        # Get model ID with caching consideration
        IrModel = self.env['ir.model'].sudo()
        model = IrModel.search([('model', '=', res_model)], limit=1)

        if not model:
            return

        # Find applicable audit configurations for this model
        audits = self.sudo().search([('model_ids', 'in', model.id)])

        if not audits:
            return

        # Filter audits based on operation type and user
        applicable_audits = audits.filtered(
            lambda a: self._is_operation_tracked(operation_type, a) and
                      self._is_user_tracked(a)
        )

        if not applicable_audits:
            return

        # Prepare common log values
        current_time = fields.Datetime.now()
        user_id = self.env.user.id
        AuditLog = self.env['user.audit.log'].sudo()

        # Handle delete operation (may have multiple record IDs)
        if operation_type == 'delete':
            if not res_id:
                return

            # Ensure res_id is a list
            record_ids = res_id if isinstance(res_id, list) else [res_id]

            # Batch create log entries
            log_vals = [
                {
                    'user_id': user_id,
                    'model_id': model.id,
                    'record': rec_id,
                    'operation_type': 'delete',
                    'date': current_time,
                }
                for rec_id in record_ids
            ]
            AuditLog.create(log_vals)
        else:
            # Single log entry for create/read/write operations
            AuditLog.create({
                'user_id': user_id,
                'model_id': model.id,
                'operation_type': operation_type,
                'record': res_id,
                'date': current_time,
            })