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
import logging

_logger = logging.getLogger(__name__)

WATCHED_FIELDS = (
    'name', 'ods_code', 'street', 'street2', 'city', 'zip', 'phone',
    'establishment_date',
)

TRUST_STATUS_MAP = {
    'active': 'active',
    'inactive': 'dissolved',
}

ALLOWED_TRANSITIONS = {
    'draft': ['under_review'],
    'under_review': ['active'],
    'active': ['special_measures', 'suspended', 'merging', 'dissolved'],
    'special_measures': ['active', 'suspended', 'merging', 'dissolved'],
    'suspended': ['active', 'special_measures', 'merging', 'dissolved'],
    'merging': ['dissolved'],
    'dissolved': [],
}

ODS_FIELD_MAP = {
    'name': 'name',
    'ods_code': 'ods_code',
    'address_line1': 'street',
    'address_line2': 'street2',
    'city': 'city',
    'postcode': 'zip',
    'phone': 'phone',
    'operational_start_date': 'establishment_date',
}


class OdsConflictDetector:
    """Detect differences and potential conflicts between local trust records and ODS data."""

    def __init__(self, env):
        """Initialize the conflict detector with the current Odoo environment."""
        self.env = env

    def detect(self, parsed: dict, trust, ods_org) -> list:
        """Compare parsed ODS organization data against a trust record to identify field/state conflicts."""
        conflicts = []


        # Note: Do not early-return here even if raw_payload_hash matches,
        # because the local trust might have manual modifications that need
        # to be flagged as conflicts.


        ods_status = TRUST_STATUS_MAP.get(parsed.get('status', 'active'), 'dissolved')
        if ods_status != trust.state:
            current = trust.state or 'draft'
            allowed = ALLOWED_TRANSITIONS.get(current, [])
            if ods_status not in allowed:
                conflicts.append({
                    'type': 'disallowed_state_change',
                    'field_name': 'state',
                    'field_label': 'Status',
                    'current_value': current,
                    'ods_value': ods_status,
                })

        provenance = {p.field_name: p for p in trust.ods_provenance_ids}

        for ods_key, trust_field in ODS_FIELD_MAP.items():
            if trust_field not in WATCHED_FIELDS:
                continue
            ods_val = parsed.get(ods_key)
            trust_val = getattr(trust, trust_field, None)
            if ods_val == trust_val:
                continue
            if ods_val is None and not trust_val:
                continue

            prov = provenance.get(trust_field)
            if prov and not prov.auto_update:
                conflicts.append({
                    'type': 'auto_update_disabled',
                    'field_name': trust_field,
                    'field_label': trust._fields[trust_field].string if trust_field in trust._fields else trust_field,
                    'current_value': str(trust_val or ''),
                    'ods_value': str(ods_val or ''),
                })
            elif prov and prov.source == 'manual':
                conflicts.append({
                    'type': 'field_diff',
                    'field_name': trust_field,
                    'field_label': trust._fields[trust_field].string if trust_field in trust._fields else trust_field,
                    'current_value': str(trust_val or ''),
                    'ods_value': str(ods_val or ''),
                    'manual_source_user_id': prov.last_updated_by_user_id.id if prov.last_updated_by_user_id else None,
                    'manual_source_date': prov.last_updated_at,
                })

        role_mapping = self.env['nhs.ods.role.mapping'].search([
            ('role_code', '=', parsed.get('primary_role_code')),
            ('active', '=', True),
        ], order='sequence', limit=1)
        if role_mapping and role_mapping.trust_type_id and role_mapping.trust_type_id != trust.trust_type_id:
            conflicts.append({
                'type': 'role_demotion',
                'field_name': 'trust_type_id',
                'field_label': 'Trust Type',
                'current_value': trust.trust_type_id.name if trust.trust_type_id else '',
                'ods_value': role_mapping.trust_type_id.name,
            })

        return conflicts
