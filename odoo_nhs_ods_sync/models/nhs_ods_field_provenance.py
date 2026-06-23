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



class NhsOdsFieldProvenance(models.Model):
    """Track the data source (manual vs ODS sync) for each fields on NHS Trust records."""
    _name = 'nhs.ods.field.provenance'
    _description = 'Tracks the source (manual vs ODS) of each field on each NHS Trust'
    _order = 'trust_id, field_name'

    trust_id = fields.Many2one(
        'nhs.trust',
        string='Trust',
        required=True,
        ondelete='cascade',
        index=True,
        help="Target trust record.",
    )
    field_name = fields.Char(
        string='Field (technical)',
        required=True,
        index=True,
        help="Technical field name e.g. 'name', 'phone'.",
    )
    source = fields.Selection([
        ('manual', 'Manual Edit'),
        ('ods', 'ODS Sync'),
        ('unknown', 'Unknown'),
    ], string='Source', required=True, default='unknown',
        help="Origin source of the field value.",
    )
    last_updated_at = fields.Datetime(
        string='Last Updated At',
        required=True,
        default=fields.Datetime.now,
        help="Date and time when the field value was last updated.",
    )

    last_updated_by_user_id = fields.Many2one(
        'res.users',
        string='Last Updated By',
        help="User who set the value (manual sources only).",
    )
    last_sync_run_id = fields.Many2one(
        'nhs.ods.sync.run',
        string='Last Sync Run',
        ondelete='set null',
        help="Sync run that set the value (ODS sources only).",
    )
    auto_update = fields.Boolean(
        string='Auto Update',
        default=True,
        help="When False, the sync engine will always raise a conflict instead of auto-updating.",
    )

    @api.depends('trust_id.name', 'field_name')
    def _compute_display_name(self):
        """Compute display name using trust name and field name."""
        for record in self:
            trust_name = record.trust_id.name or 'Unknown Trust'
            record.display_name = f"{trust_name}: {record.field_name}"

    _trust_field_uniq = models.Constraint(
        'unique(trust_id, field_name)',
        'One provenance row per field per trust.',
    )

