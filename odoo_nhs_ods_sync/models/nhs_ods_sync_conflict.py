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
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class NhsOdsSyncConflict(models.Model):
    """Represent field-level discrepancies between ODS values and manual local overrides."""
    _name = 'nhs.ods.sync.conflict'
    _inherit = ['mail.thread']
    _description = 'ODS sync field-level conflict pending resolution'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    sync_run_id = fields.Many2one(
        'nhs.ods.sync.run',
        string='Sync Run',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sync_detail_id = fields.Many2one(
        'nhs.ods.sync.detail',
        string='Sync Detail',
        required=True,
        ondelete='cascade',
    )
    trust_id = fields.Many2one(
        'nhs.trust',
        string='Trust',
        required=True,
        ondelete='cascade',
        index=True,
    )
    ods_organisation_id = fields.Many2one(
        'nhs.ods.organisation',
        string='ODS Cache Entry',
        required=True,
        ondelete='cascade',
    )
    field_name = fields.Char(
        string='Field (technical)',
        required=True,
        help="Technical field name e.g. 'name', 'phone', 'street'.",
    )
    field_label = fields.Char(
        string='Field Label',
        help="Human-readable label resolved at conflict-creation time.",
    )
    current_value = fields.Char(string='Current Value (local)', help="Current local value stored in Odoo.")
    ods_value = fields.Char(string='ODS Value', help="Value retrieved from the ODS API.")
    conflict_type = fields.Selection([
        ('field_diff', 'Manual Edit Conflict'),
        ('disallowed_state_change', 'Disallowed State Change'),
        ('auto_update_disabled', 'Auto-Update Disabled'),
        ('role_demotion', 'Role / Type Change'),
    ], string='Conflict Type', default='field_diff')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('resolved_keep_local', 'Kept Local'),
        ('resolved_use_ods', 'Accepted ODS'),
        ('ignored', 'Ignored'),
        ('superseded', 'Superseded'),
    ], string='State', required=True, default='pending', tracking=True)
    resolved_by_id = fields.Many2one('res.users', string='Resolved By')
    resolved_at = fields.Datetime(string='Resolved At')
    resolution_note = fields.Text(string='Resolution Note')
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
    )

    @api.depends('trust_id', 'field_label', 'field_name')
    def _compute_display_name(self):
        """Compute display name formatting for the conflict."""
        for rec in self:
            label = rec.field_label or rec.field_name or ''
            trust = rec.trust_id.name if rec.trust_id else ''
            rec.display_name = f'Conflict on {trust}.{label}' if trust else label

    def action_keep_local(self):
        """Resolve the conflict by keeping the local manual value."""
        for rec in self.filtered(lambda r: r.state == 'pending'):
            rec.write({
                'state': 'resolved_keep_local',
                'resolved_by_id': self.env.user.id,
                'resolved_at': fields.Datetime.now(),
            })
            if rec.trust_id:
                rec.trust_id.message_post(
                    body=_("ODS Conflict on '%(field)s' resolved: kept local value '%(val)s'.") % {
                        'field': rec.field_label or rec.field_name,
                        'val': rec.current_value or '',
                    }
                )

    def action_use_ods(self):
        """Resolve the conflict by accepting and writing the ODS value."""
        for rec in self.filtered(lambda r: r.state == 'pending'):
            if rec.trust_id and rec.field_name and rec.ods_value is not None:
                ctx = {'nhs_ods_sync': True, 'approved_state_change': True}
                rec.trust_id.with_context(**ctx).write({rec.field_name: rec.ods_value or False})
            rec.write({
                'state': 'resolved_use_ods',
                'resolved_by_id': self.env.user.id,
                'resolved_at': fields.Datetime.now(),
            })
            if rec.trust_id:
                rec.trust_id.message_post(
                    body=_("ODS Conflict on '%(field)s' resolved: accepted ODS value '%(val)s'.") % {
                        'field': rec.field_label or rec.field_name,
                        'val': rec.ods_value or '',
                    }
                )

    def action_ignore(self):
        """Resolve the conflict by ignoring it and disabling future auto-updates."""
        for rec in self.filtered(lambda r: r.state == 'pending'):
            if not rec.resolution_note:
                raise UserError(("Please provide a resolution note before ignoring a conflict."))
            prov = self.env['nhs.ods.field.provenance'].search([
                ('trust_id', '=', rec.trust_id.id),
                ('field_name', '=', rec.field_name),
            ], limit=1)
            if prov:
                prov.auto_update = False
            rec.write({
                'state': 'ignored',
                'resolved_by_id': self.env.user.id,
                'resolved_at': fields.Datetime.now(),
            })
            if rec.trust_id:
                rec.trust_id.message_post(
                    body=_("ODS Conflict on '%(field)s' ignored. Reason: %(note)s") % {
                        'field': rec.field_label or rec.field_name,
                        'note': rec.resolution_note,
                    }
                )

    def action_view_trust(self):
        """Return an action opening the form view of the affected trust."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nhs.trust',
            'res_id': self.trust_id.id,
            'view_mode': 'form',
        }

