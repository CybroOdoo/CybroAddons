# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo import api, exceptions, fields, models, _

_logger = logging.getLogger(__name__)


class WmAuditLog(models.Model):
    """Immutable audit log repository storing field-level changes across auditable models."""
    _name = 'wm.audit.log'
    _description = 'Waste Management Audit Log'
    _order = 'log_date desc, id desc'

    model_id = fields.Many2one('ir.model', string='Model', required=True, index=True, ondelete='cascade')
    res_id = fields.Integer(string='Record ID', required=True, index=True)
    field_name = fields.Char(string='Field Name')
    old_value = fields.Text(string='Old Value')
    new_value = fields.Text(string='New Value')
    user_id = fields.Many2one('res.users', string='Responsible User', required=True, default=lambda self: self.env.user)
    log_date = fields.Datetime(string='Timestamp', required=True, default=fields.Datetime.now)
    action = fields.Selection([
        ('create', 'Create'),
        ('write', 'Write'),
        ('unlink', 'Delete'),
    ], string='Action', required=True)
    record_name = fields.Char(string='Record Name', compute='_compute_record_name')

    @api.depends('model_id', 'res_id')
    def _compute_record_name(self):
        """
        Resolve the display name of the audited source record by calling name_get on
        the target model, providing a readable reference in the audit log list view.
        """
        for log in self:
            if log.model_id and log.res_id:
                try:
                    record = self.env[log.model_id.model].browse(log.res_id)
                    # If record is deleted, display_name might be False or throw error
                    if record.exists():
                        log.record_name = record.display_name or f"{log.model_id.name} ({log.res_id})"
                    else:
                        log.record_name = f"{log.model_id.name} ({log.res_id}) [Deleted]"
                except Exception as e:
                    _logger.debug("Failed to resolve record name for %s(%s): %s", log.model_id.model, log.res_id, e)
                    log.record_name = f"{log.model_id.name} ({log.res_id})"
            else:
                log.record_name = "Unknown"

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to prevent any modification of audit log entries after
        they are written; raises UserError if an attempt to update an existing
        log record is detected.
        """
        return super().create(vals_list)

    def write(self, vals):
        """ Override write to implement business validations and side effects."""
        raise exceptions.UserError(_('Audit records cannot be edited by any user, including administrators.'))

    def unlink(self):
        """ Override unlink to handle cascading cleanup or prevent invalid deletions. """
        raise exceptions.UserError(_('Audit records cannot be deleted by any user, including administrators.'))
