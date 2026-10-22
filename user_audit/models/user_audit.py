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
#############################################################################
from odoo import api, fields, models


class UserAudit(models.Model):
    """Manage user audit configurations for tracking activities on selected
    users and models.
    """

    _name = "user.audit"
    _description = "User Audit Log Configuration"

    name = fields.Char(
        required=True,
        string="Name",
        help="Name of the log.",
    )

    is_read = fields.Boolean(
        string="Read",
        help="Enable this option to track all read activities. "
             "Tracking read activities may increase the size of the log "
             "and can affect database performance.",
    )

    is_write = fields.Boolean(
        string="Write",
        help="Enable this option to track all write activities.",
    )

    is_create = fields.Boolean(
        string="Create",
        help="Enable this option to track all create activities.",
    )

    is_delete = fields.Boolean(
        string="Delete",
        help="Enable this option to track all delete activities.",
    )

    is_all_users = fields.Boolean(
        string="All Users",
        help="Enable this option to track activities of all users.",
    )

    user_ids = fields.Many2many(
        "res.users",
        string="Users",
        help="Select the users whose activities should be tracked.",
    )

    model_ids = fields.Many2many(
        "ir.model",
        string="Models",
        help="Select the models whose activities should be tracked.",
    )

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
        valid_operations = {
            'create': 'create',
            'read': 'read',
            'write': 'write',
            'delete': 'unlink',
        }
        if operation_type not in valid_operations:
            return

        if not res_model or res_model not in self.env:
            return

        # Check that the calling user actually has permission on the target model
        op_check = valid_operations[operation_type]
        if not self.env[res_model].has_access(op_check):
            return

        IrModel = self.env['ir.model'].sudo()
        model = IrModel.search([('model', '=', res_model)], limit=1)

        if not model:
            return

        audits = self.sudo().search([('model_ids', 'in', model.id)])

        if not audits:
            return

        applicable_audits = audits.filtered(
            lambda a: self._is_operation_tracked(operation_type, a) and
                      self._is_user_tracked(a)
        )

        if not applicable_audits:
            return

        current_time = fields.Datetime.now()
        user_id = self.env.user.id
        AuditLog = self.env['user.audit.log'].sudo()

        if operation_type == 'delete':
            if not res_id:
                return

            record_ids = res_id if isinstance(res_id, list) else [res_id]

            log_vals = [
                {
                    'user_id': user_id,
                    'model_id': model.id,
                    'record': rec_id,
                    'operation_type': 'delete',
                    'date': current_time,
                }
                for rec_id in record_ids
                if rec_id
            ]
            if log_vals:
                AuditLog.create(log_vals)
        else:
            if not res_id:
                return

            AuditLog.create({
                'user_id': user_id,
                'model_id': model.id,
                'operation_type': operation_type,
                'record': res_id,
                'date': current_time,
            })
