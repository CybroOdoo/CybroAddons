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
from odoo import models, fields, api


class NhsOdsSyncDetail(models.Model):
    """Represent execution details for a specific organisation in a sync run."""
    _name = 'nhs.ods.sync.detail'
    _description = 'Per-organisation sync result'
    _order = 'sync_run_id desc, ods_code'
    _rec_name = 'display_name'

    sync_run_id = fields.Many2one(
        'nhs.ods.sync.run',
        string='Sync Run',
        required=True,
        ondelete='cascade',
        index=True,
        help="Parent sync run record.",
    )
    ods_code = fields.Char(
        string='ODS Code',
        required=True,
        help="ODS code of the processed organisation.",
    )
    ods_organisation_id = fields.Many2one(
        'nhs.ods.organisation',
        string='ODS Cache Entry',
        ondelete='set null',
        help="Associated ODS cache entry for the organization.",
    )
    outcome = fields.Selection([
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('unchanged', 'Unchanged'),
        ('conflict', 'Conflict'),
        ('error', 'Error'),
        ('skipped', 'Skipped'),
        ('would_update', 'Would Update (dry run)'),
    ], string='Outcome', required=True, help="Outcome of syncing this specific organisation.")
    trust_id = fields.Many2one(
        'nhs.trust',
        string='Trust',
        ondelete='set null',
        help="Linked Odoo NHS trust record.",
    )
    icb_id = fields.Many2one(
        'nhs.icb',
        string='ICB',
        ondelete='set null',
        help="Linked Odoo ICB record.",
    )
    changed_fields = fields.Char(
        string='Changed Fields',
        help="Comma-separated list of nhs.trust fields modified.",
    )
    conflict_ids = fields.One2many(
        'nhs.ods.sync.conflict',
        'sync_detail_id',
        string='Conflicts',
    )
    error_message = fields.Text(
        string='Error Message',
        help="Error traceback message if the sync failed for this organization.",
    )
    skip_reason = fields.Char(
        string='Skip Reason',
        help="Reason for skipping the synchronization of this organization.",
    )
    duration_ms = fields.Integer(
        string='Duration (ms)',
        help="Processing duration in milliseconds.",
    )
    diff_json = fields.Text(
        string='Diff (JSON)',
        help="For dry-run would_update rows: JSON representation of what would change.",
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
    )

    @api.depends('ods_code', 'outcome', 'trust_id')
    def _compute_display_name(self):
        """Compute display name for the sync detail."""
        outcome_labels = dict(self._fields['outcome'].selection)
        for rec in self:
            outcome_str = outcome_labels.get(rec.outcome, rec.outcome or '')
            trust_name = rec.trust_id.name if rec.trust_id else ''
            if trust_name:
                rec.display_name = f"{rec.ods_code} ({trust_name}) — {outcome_str}"
            else:
                rec.display_name = f"{rec.ods_code} — {outcome_str}"

