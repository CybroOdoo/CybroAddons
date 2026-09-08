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

from odoo import api, models
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


class WmAuditMixin(models.AbstractModel):
    """Abstract mixin model providing automatic audit logging and status change tracking."""
    _name = 'wm.audit.mixin'
    _description = 'Waste Management Audit Mixin'

    def _is_audit_trail_enabled(self):
        """ Helper to correctly check if audit logging is enabled. """
        param = self.env['ir.config_parameter'].sudo().get_param('wm_base.group_wm_audit_trail', 'False')
        return str(param).lower() in ('true', '1', 'yes')

    def _get_audit_value(self, field_name, value):
        """
        Extract a human-readable display value for a given field value,
        resolving Many2one display names and selection labels to produce
        meaningful audit log entries.
        """
        if value is False or value is None or value == "":
            return ""
        field = self._fields.get(field_name)
        if not field:
            val_str = str(value)
            return val_str if len(val_str) <= 200 else val_str[:197] + '...'

        if field.type == 'binary':
            if value:
                try:
                    if isinstance(value, bytes):
                        size_kb = len(value) / 1024
                    elif isinstance(value, str):
                        size_kb = (len(value) * 0.75) / 1024
                    else:
                        size_kb = 0
                    return f"[Binary File: {size_kb:.1f} KB]"
                except Exception as e:
                    _logger.debug("Failed to calculate binary file size in audit: %s", e)
                    return "[Binary File]"
            return ""
        elif field.type == 'html':
            if value:
                try:
                    clean_text = html2plaintext(str(value)).strip()
                    clean_text = " ".join(clean_text.split())
                    return clean_text if len(clean_text) <= 200 else clean_text[:197] + '...'
                except Exception as e:
                    _logger.debug("Failed to clean html text in audit: %s", e)
                    return str(value)[:200]
            return ""
        elif field.type == 'many2one':
            try:
                if isinstance(value, models.BaseModel):
                    return value.display_name if value.exists() else f"Deleted ({value.id})"
                elif value:
                    record = self.env[field.comodel_name].browse(int(value))
                    return record.display_name if record.exists() else f"Deleted ({value})"
                return ""
            except Exception as e:
                _logger.debug("Failed to resolve many2one display name in audit: %s", e)
                return str(value)
        elif field.type == 'selection':
            try:
                selection = dict(field._description_selection(self.env))
                return selection.get(value, str(value))
            except Exception as e:
                _logger.debug("Failed to resolve selection value in audit: %s", e)
                return str(value)
        elif field.type in ('many2many', 'one2many'):
            try:
                if isinstance(value, (set, list, tuple, models.BaseModel)):
                    return f"{len(value)} record(s)"
                return str(value)
            except Exception as e:
                _logger.debug("Failed to format x2many record count in audit: %s", e)
                return str(value)
        elif field.type == 'boolean':
            return "Yes" if value else "No"

        res_str = str(value)
        return res_str if len(res_str) <= 200 else res_str[:197] + '...'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override ORM create to stamp audit metadata (created_by, created_at) on
        every new record before delegating to super(), ensuring all child
        models carry a consistent audit trail.
        """
        records = super().create(vals_list)
        if not self._is_audit_trail_enabled():
            return records

        model_id = self.env['ir.model']._get(self._name)
        log_vals_list = []
        for record in records:
            rec_name = record.display_name if hasattr(record, 'display_name') and record.display_name else f"{self._name} ({record.id})"
            log_vals_list.append({
                'model_id': model_id.id,
                'res_id': record.id,
                'field_name': 'Record Created',
                'old_value': "",
                'new_value': rec_name,
                'user_id': self.env.user.id,
                'action': 'create'
            })
        if log_vals_list:
            self.env['wm.audit.log'].sudo().create(log_vals_list)
        return records

    def write(self, vals):
        """
        Override ORM write to record the last modification author and timestamp
        on every update, maintaining an accurate audit trail for compliance and
        regulatory review.
        """
        if not self._is_audit_trail_enabled():
            return super().write(vals)

        model_id = self.env['ir.model']._get(self._name)

        # High-value compliance & tracked fields to audit (avoids duplicate logging of trivial UI/compute fields)
        def _is_auditable_field(fname):
            """
            Determine whether a given field should be tracked in the audit log
            based on the model's configured auditable field list, excluding
            system and computed fields.
            """
            if fname in ['write_date', 'write_uid', 'create_date', 'create_uid', '__last_update']:
                return False
            fdef = self._fields.get(fname)
            if not fdef:
                return False
            # Always audit state/status, identity, compliance fields, or fields with tracking enabled
            if fname in ('state', 'status', 'name', 'code', 'hazardous', 'is_received', 'partner_id',
                         'disposal_facility_id', 'vehicle_id', 'driver_id', 'stream'):
                return True
            return getattr(fdef, 'tracking', False) or getattr(fdef, 'audit', False)

        auditable_fields = [f for f in vals.keys() if _is_auditable_field(f)]

        # Track old values BEFORE write
        old_values = {}
        if auditable_fields:
            for record in self:
                old_rec = {}
                for field in auditable_fields:
                    field_def = self._fields.get(field)
                    if field_def.type == 'many2one':
                        old_rec[field] = record[field].id or False
                    elif field_def.type in ('many2many', 'one2many'):
                        old_rec[field] = set(record[field].ids)
                    else:
                        old_rec[field] = record[field]
                old_values[record.id] = old_rec

        res = super().write(vals)

        # Log changes AFTER write
        if auditable_fields:
            log_vals_list = []
            for record in self:
                for field in auditable_fields:
                    field_def = self._fields.get(field)
                    old_val = old_values[record.id].get(field)

                    if field_def.type == 'many2one':
                        new_val_cmp = record[field].id or False
                    elif field_def.type in ('many2many', 'one2many'):
                        new_val_cmp = set(record[field].ids)
                    else:
                        new_val_cmp = record[field]

                    if old_val != new_val_cmp:
                        field_label = field_def.string if field_def else field

                        log_vals_list.append({
                            'model_id': model_id.id,
                            'res_id': record.id,
                            'field_name': field_label,
                            'old_value': self._get_audit_value(field, old_val),
                            'new_value': self._get_audit_value(field, new_val_cmp),
                            'user_id': self.env.user.id,
                            'action': 'write'
                        })

                        if field in ('state', 'status'):
                            old_st = self._get_audit_value(field, old_val)
                            new_st = self._get_audit_value(field, new_val_cmp)
                            reason = self.env.context.get('status_transition_reason', 'State Change')
                            record.log_status_transition(old_st, new_st, reason=reason)
            if log_vals_list:
                self.env['wm.audit.log'].sudo().create(log_vals_list)
        return res

    def unlink(self):
        """ Override unlink to handle cascading cleanup or prevent invalid deletions. """
        if self._is_audit_trail_enabled():
            model_id = self.env['ir.model']._get(self._name)
            log_vals_list = []
            for record in self:
                rec_name = record.display_name if hasattr(record, 'display_name') and record.display_name else f"{self._name} ({record.id})"
                log_vals_list.append({
                    'model_id': model_id.id,
                    'res_id': record.id,
                    'field_name': 'Record Deleted',
                    'old_value': rec_name,
                    'new_value': '[Deleted]',
                    'user_id': self.env.user.id,
                    'action': 'unlink'
                })
            if log_vals_list:
                self.env['wm.audit.log'].sudo().create(log_vals_list)
        return super().unlink()

    def log_status_transition(self, old_state, new_state, reason=False):
        """
        Record a status change event to the wm.status.transition.log, capturing
        the previous state, new state, timestamp, and triggering user for
        compliance audit trails.
        """
        if not self._is_audit_trail_enabled():
            return False

        model_id = self.env['ir.model']._get(self._name)
        trans_vals_list = []
        for record in self:
            trans_vals_list.append({
                'model_id': model_id.id,
                'res_id': record.id,
                'old_state': old_state,
                'new_state': new_state,
                'reason': reason or 'Manual State Change',
                'user_id': self.env.user.id
            })
        if trans_vals_list:
            self.env['wm.status.transition.log'].sudo().create(trans_vals_list)
        return True
