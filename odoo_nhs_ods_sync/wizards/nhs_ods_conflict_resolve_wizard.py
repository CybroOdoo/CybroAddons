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


class NhsOdsConflictResolveWizard(models.TransientModel):
    """Transient wizard to bulk resolve pending ODS field conflicts."""
    _name = 'nhs.ods.conflict.resolve.wizard'
    _description = 'NHS ODS Bulk Conflict Resolution Wizard'

    conflict_ids = fields.Many2many(
        'nhs.ods.sync.conflict',
        string='Conflicts to Resolve',
        help="Conflicts selected for bulk resolution.",
    )
    resolution = fields.Selection([
        ('accept_ods', 'Accept ODS Values'),
        ('keep_manual', 'Keep Local Values'),
        ('ignore', 'Ignore (suppress future conflicts)'),
    ], string='Resolution', required=True,
        help="Choose whether to accept ODS values, keep manual local changes, or ignore them.",
    )
    reason = fields.Text(
        string='Reason',
        help="Required when resolution is 'Ignore'.",
    )
    set_auto_update_false = fields.Boolean(
        string='Disable auto-update for these fields',
        help="When True, future syncs will always raise a conflict instead of auto-resolving.",
    )

    @api.model
    def default_get(self, fields_list):
        """Prefill the conflicts to resolve based on the active_ids in context."""
        res = super().default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if 'conflict_ids' in fields_list and active_ids:
            res['conflict_ids'] = [(6, 0, active_ids)]
        return res

    def action_confirm(self):
        """Process and apply the selected bulk resolution (Accept ODS, Keep Local, or Ignore)."""
        self.ensure_one()
        if self.resolution == 'ignore' and not self.reason:
            raise UserError(_("Please provide a reason when ignoring conflicts."))

        conflicts = self.conflict_ids.filtered(lambda c: c.state == 'pending')
        if not conflicts:
            raise UserError(_("No pending conflicts selected."))

        if self.resolution == 'accept_ods':
            for conflict in conflicts:
                conflict.action_use_ods()
        elif self.resolution == 'keep_manual':
            for conflict in conflicts:
                conflict.action_keep_local()
        elif self.resolution == 'ignore':
            for conflict in conflicts:
                conflict.resolution_note = self.reason
                conflict.action_ignore()
                if self.set_auto_update_false:
                    prov = self.env['nhs.ods.field.provenance'].search([
                        ('trust_id', '=', conflict.trust_id.id),
                        ('field_name', '=', conflict.field_name),
                    ], limit=1)
                    if prov:
                        prov.auto_update = False

        resolved_count = len(conflicts)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Conflicts Resolved'),
                'message': _('Resolved %(count)s conflicts.', count=resolved_count),
                'sticky': False,
                'type': 'success',
            },
        }

