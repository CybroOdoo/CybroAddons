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

PROVENANCE_WATCHED_FIELDS = (
    'name', 'ods_code', 'state', 'street', 'street2', 'city', 'zip', 'phone',
    'establishment_date', 'foundation_trust', 'trust_type_id',
)


class NhsTrust(models.Model):
    """Extend core nhs.trust model to add fields and features for ODS integration."""
    _inherit = 'nhs.trust'

    ods_org_id = fields.Many2one(
        'nhs.ods.organisation',
        string='ODS Cache Entry',
        ondelete='set null',
        help="Reverse link to the cached ODS payload.",
    )
    ods_last_synced_at = fields.Datetime(
        string='Last ODS Sync',
        help="Timestamp of the most recent successful sync that touched this trust.",
    )
    ods_provenance_ids = fields.One2many(
        'nhs.ods.field.provenance',
        'trust_id',
        string='Field Provenance',
        help="All field provenance records tracking modifications for this trust.",
    )
    ods_pending_conflict_count = fields.Integer(
        string='Pending Conflicts',
        compute='_compute_ods_pending_conflict_count',
        help="Count of open ODS conflicts on this trust.",
    )

    def _compute_ods_pending_conflict_count(self):
        """Compute the count of pending conflicts for this trust."""
        for trust in self:
            trust.ods_pending_conflict_count = self.env['nhs.ods.sync.conflict'].search_count([
                ('trust_id', '=', trust.id),
                ('state', '=', 'pending'),
            ])

    # NB: the geographic/governance constraints already honour the
    # ``nhs_ods_sync`` context bypass at their definition sites
    # (``odoo_nhs_trust_management`` and ``odoo_nhs_uk_regions`` respectively),
    # so this module does not re-declare them. Overriding _check_governance_link
    # here would break standalone installs, since that method and welsh_lhb_id
    # only exist when odoo_nhs_uk_regions is installed (not a dependency).

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to record field provenance for manual creations."""
        records = super().create(vals_list)
        if not self.env.context.get('nhs_ods_sync'):
            for record, vals in zip(records, vals_list):
                record._upsert_provenance(vals, source='manual')
        return records

    def write(self, vals):
        """Override write to track field provenance for manual edits and bypass state guard for sync."""
        if self.env.context.get('nhs_ods_sync') and 'state' in vals:
            state = vals.pop('state')
            result = super().write(vals)
            super(models.Model, self).write({'state': state})
            vals['state'] = state
        else:
            result = super().write(vals)
        if not self.env.context.get('nhs_ods_sync'):
            for record in self:
                record._upsert_provenance(vals, source='manual')
        return result

    def _upsert_provenance(self, vals, source):
        """Upsert the field provenance tracking entry for the specified field and source."""
        Provenance = self.env['nhs.ods.field.provenance'].sudo()
        sync_run = self.env.context.get('nhs_ods_sync_run_id')
        for fname in PROVENANCE_WATCHED_FIELDS:
            if fname not in vals:
                continue
            existing = Provenance.search([
                ('trust_id', '=', self.id),
                ('field_name', '=', fname),
            ], limit=1)
            prov_vals = {
                'source': source,
                'last_updated_at': fields.Datetime.now(),
            }
            if source == 'manual':
                prov_vals['last_updated_by_user_id'] = self.env.user.id
            elif source == 'ods' and sync_run:
                prov_vals['last_sync_run_id'] = sync_run
            if existing:
                existing.write(prov_vals)
            else:
                Provenance.create({
                    'trust_id': self.id,
                    'field_name': fname,
                    **prov_vals,
                })

    def action_refresh_from_ods(self):
        """Query ODS API to refresh cache and apply modifications to the trust."""
        self.ensure_one()
        if not self.ods_code:
            from odoo.exceptions import UserError
            raise UserError(("This trust has no ODS code — cannot refresh from ODS."))
        if self.ods_org_id:
            self.ods_org_id.refresh_from_ods()
            self.ods_org_id.apply_to_trust()
        else:
            ods_org = self.env['nhs.ods.organisation'].search([('ods_code', '=', self.ods_code)], limit=1)
            if not ods_org:
                ods_org = self.env['nhs.ods.organisation'].create({
                    'ods_code': self.ods_code,
                    'name': self.name,
                })
            ods_org.refresh_from_ods()
            ods_org.apply_to_trust()
            self.ods_org_id = ods_org
        self.ods_last_synced_at = fields.Datetime.now()

    def action_view_provenance(self):
        """Return an action displaying the field provenance details for the trust."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': ('Field Provenance'),
            'res_model': 'nhs.ods.field.provenance',
            'view_mode': 'list',
            'domain': [('trust_id', '=', self.id)],
            'context': {'default_trust_id': self.id},
        }

    def action_view_conflicts(self):
        """Return an action displaying the pending ODS conflicts for the trust."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': ('ODS Conflicts'),
            'res_model': 'nhs.ods.sync.conflict',
            'view_mode': 'kanban,list,form',
            'domain': [('trust_id', '=', self.id), ('state', '=', 'pending')],
            'context': {'default_trust_id': self.id},
        }

