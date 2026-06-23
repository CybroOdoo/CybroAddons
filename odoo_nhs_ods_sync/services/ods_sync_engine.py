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
import json
import logging
import time

from odoo import fields

from .ods_api_client import OdsApiClient
from .ods_payload_parser import parse_ods_payload
from .ods_conflict_detector import OdsConflictDetector, ALLOWED_TRANSITIONS, TRUST_STATUS_MAP

_logger = logging.getLogger(__name__)

COUNTRY_MAP = {
    'ENGLAND': 'GB',
    'WALES': 'GB',
    'SCOTLAND': 'GB',
    'NORTHERN IRELAND': 'GB',
}


class OdsSyncEngine:
    """Core synchronization engine to fetch, parse, and apply ODS data to Odoo models."""

    def __init__(self, env, run):
        """Initialize the sync engine with environment and run contexts."""
        self.env = env
        self.run = run
        self.api = OdsApiClient(env)
        self.detector = OdsConflictDetector(env)
        self._is_dry_run = (run.run_type == 'dry_run')

    def run_full(self):
        """Perform full synchronization for all mapped roles."""
        mappings = self.env['nhs.ods.role.mapping'].search([('active', '=', True)])
        fetched = set()
        for mapping in mappings:
            if self.run.cancel_requested:
                break
            orgs = self.api.search_organisations(PrimaryRoleId=mapping.role_code, Status='Active')
            for org_stub in orgs:
                if self.run.cancel_requested:
                    break
                ods_code = self._extract_code(org_stub)
                if ods_code and ods_code not in fetched:
                    fetched.add(ods_code)
                    self._process_org_stub(org_stub)
                    self._commit_progress()  # visible to other sessions immediately
        self.run.fetched_count = len(fetched)

    def run_delta(self, since_date):
        """Perform incremental synchronization starting from since_date."""
        mappings = self.env['nhs.ods.role.mapping'].search([('active', '=', True)])
        fetched = set()
        for mapping in mappings:
            if self.run.cancel_requested:
                break
            if since_date:
                orgs = self.api.search_organisations(
                    PrimaryRoleId=mapping.role_code,
                    LastChangeDate=str(since_date)
                )
            else:
                orgs = self.api.search_organisations(
                    PrimaryRoleId=mapping.role_code,
                    Status='Active'
                )
            for org_stub in orgs:
                if self.run.cancel_requested:
                    break
                ods_code = self._extract_code(org_stub)
                if ods_code and ods_code not in fetched:
                    fetched.add(ods_code)
                    self._process_org_stub(org_stub)
                    self._commit_progress()  # visible to other sessions immediately
        self.run.fetched_count = len(fetched)

    def _commit_progress(self):
        """Flush ORM cache and commit so progress counters are visible while running."""
        try:
            self.env.cr.flush()
            self.env.cr.commit()
        except Exception:
            pass

    def run_single(self, ods_code):
        """Perform targeted synchronization for a single ODS code."""
        t0 = time.monotonic()
        try:
            with self.env.cr.savepoint():
                raw = self.api.get_organisation(ods_code)
                org_data = raw.get('Organisation', raw)
                self.run.fetched_count = 1
                self._process_org(org_data)
        except Exception as exc:
            _logger.exception("run_single failed for %s", ods_code)
            try:
                with self.env.cr.savepoint():
                    self._record_detail(
                        ods_code=ods_code,
                        outcome='error',
                        error_message=str(exc),
                        duration_ms=int((time.monotonic() - t0) * 1000),
                    )
                    self.run.error_count += 1
            except Exception:
                _logger.exception("Failed to log single error in DB for org %s", ods_code)

    def _extract_code(self, org_stub):
        """Extract the ODS code from an organization stub dict or string."""
        if isinstance(org_stub, dict):
            oid = org_stub.get('OrgId', {})
            if isinstance(oid, dict):
                return oid.get('extension', '')
            return org_stub.get('OrgId', '')
        return ''

    def _process_org_stub(self, org_stub):
        """Fetch and process details for a single organization stub in a savepoint."""
        ods_code = self._extract_code(org_stub)
        if not ods_code:
            return

        t0 = time.monotonic()
        try:
            with self.env.cr.savepoint():
                raw = self.api.get_organisation(ods_code)
                org_data = raw.get('Organisation', raw)
                self._process_org(org_data, duration_start=t0)
        except Exception as exc:
            _logger.exception("Failed to process org %s", ods_code)
            try:
                with self.env.cr.savepoint():
                    self._record_detail(
                        ods_code=ods_code,
                        outcome='error',
                        error_message=str(exc),
                        duration_ms=int((time.monotonic() - t0) * 1000),
                    )
                    self.run.error_count += 1
                    self.run.error_log = (self.run.error_log or '') + f'\n[{ods_code}] {exc}'
            except Exception:
                _logger.exception("Failed to log detail error in DB for org %s", ods_code)

    def _process_org(self, org_data, duration_start=None):
        """Process a single organization's payload, handling caching, role mappings, and trust creation/updates."""
        t0 = duration_start or time.monotonic()
        try:

            parsed = parse_ods_payload(org_data)
        except ValueError as exc:
            _logger.warning("Skipping org — parse failed: %s", exc)
            self.run.skipped_count += 1
            return

        ods_code = parsed['ods_code']

        role_mapping = self.env['nhs.ods.role.mapping'].search([
            ('role_code', '=', parsed.get('primary_role_code')),
            ('active', '=', True),
        ], order='sequence', limit=1)

        if not role_mapping:
            ods_org = self._upsert_cache(parsed, org_data)
            self._record_detail(
                ods_code=ods_code,
                outcome='skipped',
                ods_org=ods_org,
                skip_reason=f"No role mapping for {parsed.get('primary_role_code')}",
                duration_ms=int((time.monotonic() - t0) * 1000),
            )
            self.run.skipped_count += 1
            return

        ods_org = self._upsert_cache(parsed, org_data)

        if not role_mapping.creates_trust:
            self._record_detail(
                ods_code=ods_code,
                outcome='skipped',
                ods_org=ods_org,
                skip_reason=f"Role {parsed.get('primary_role_code')} is reference-only (creates_trust=False)",
                duration_ms=int((time.monotonic() - t0) * 1000),
            )
            self.run.skipped_count += 1
            return

        trust = self._match_trust(parsed)

        if not trust:
            if self._is_dry_run:
                self._record_detail(
                    ods_code=ods_code,
                    outcome='would_update',
                    ods_org=ods_org,
                    diff_json=json.dumps({'action': 'create', 'name': parsed.get('name')}),
                    duration_ms=int((time.monotonic() - t0) * 1000),
                )
            else:
                trust = self._create_trust(parsed, ods_org, role_mapping)
                self._record_detail(
                    ods_code=ods_code,
                    outcome='created',
                    trust=trust,
                    ods_org=ods_org,
                    duration_ms=int((time.monotonic() - t0) * 1000),
                )
                self.run.created_count += 1
            return

        conflicts = self.detector.detect(parsed, trust, ods_org)

        if conflicts:
            if not self._is_dry_run:
                detail = self._record_detail(
                    ods_code=ods_code,
                    outcome='conflict',
                    trust=trust,
                    ods_org=ods_org,
                    duration_ms=int((time.monotonic() - t0) * 1000),
                )
                self._record_conflicts(conflicts, trust, ods_org, detail)
                self.run.conflict_count += 1
            else:
                self._record_detail(
                    ods_code=ods_code,
                    outcome='conflict',
                    trust=trust,
                    ods_org=ods_org,
                    diff_json=json.dumps([c['type'] for c in conflicts]),
                    duration_ms=int((time.monotonic() - t0) * 1000),
                )
        else:
            if self._is_dry_run:
                diff = self._compute_diff(parsed, trust)
                if diff:
                    self._record_detail(
                        ods_code=ods_code,
                        outcome='would_update',
                        trust=trust,
                        ods_org=ods_org,
                        diff_json=json.dumps(diff),
                        duration_ms=int((time.monotonic() - t0) * 1000),
                    )
                else:
                    self._record_detail(
                        ods_code=ods_code,
                        outcome='unchanged',
                        trust=trust,
                        ods_org=ods_org,
                        duration_ms=int((time.monotonic() - t0) * 1000),
                    )
            else:
                changed = self._apply_to_trust(parsed, trust, ods_org)
                if changed:
                    self._record_detail(
                        ods_code=ods_code,
                        outcome='updated',
                        trust=trust,
                        ods_org=ods_org,
                        changed_fields=','.join(changed),
                        duration_ms=int((time.monotonic() - t0) * 1000),
                    )
                    self.run.updated_count += 1
                else:
                    self._record_detail(
                        ods_code=ods_code,
                        outcome='unchanged',
                        trust=trust,
                        ods_org=ods_org,
                        duration_ms=int((time.monotonic() - t0) * 1000),
                    )
                    self.run.unchanged_count += 1

    def _upsert_cache(self, parsed, raw_data):
        """Create or update the cached ODS organization payload in local database."""
        OdsOrg = self.env['nhs.ods.organisation'].sudo()
        existing = OdsOrg.search([('ods_code', '=', parsed['ods_code'])], limit=1)
        vals = {
            'ods_code': parsed['ods_code'],
            'name': parsed.get('name', ''),
            'status': parsed.get('status', 'active'),
            'primary_role_code': parsed.get('primary_role_code'),
            'non_primary_role_codes': ','.join(parsed.get('all_role_codes', [])),
            'operational_start_date': parsed.get('operational_start_date'),
            'operational_end_date': parsed.get('operational_end_date'),
            'address_line1': parsed.get('address_line1'),
            'address_line2': parsed.get('address_line2'),
            'city': parsed.get('city'),
            'county': parsed.get('county'),
            'postcode': parsed.get('postcode'),
            'country_text': parsed.get('country'),
            'phone': parsed.get('phone'),
            'last_change_date': parsed.get('last_changed_at'),
            'raw_json': json.dumps(raw_data),
            'raw_payload_hash': parsed.get('raw_payload_hash'),
            'last_fetched_at': fields.Datetime.now(),
        }
        if parsed.get('primary_role_code') == 'RO165':
            vals['icb_id'] = self.env['nhs.icb'].search([('code', '=', parsed['ods_code'])], limit=1).id
        elif parsed.get('primary_role_code') == 'RO140':
            vals['health_board_id'] = self.env['nhs.health.board'].search([('code', '=', parsed['ods_code'])], limit=1).id

        if existing:
            existing.write(vals)
            return existing
        else:
            return OdsOrg.create(vals)

    def _match_trust(self, parsed):
        """Search and match a local trust record by ODS code or ODS cache relationship."""
        Trust = self.env['nhs.trust'].sudo()
        trust = Trust.search([('ods_code', '=', parsed['ods_code'])], limit=1)
        if trust:
            return trust
        ods_org = self.env['nhs.ods.organisation'].search([
            ('ods_code', '=', parsed['ods_code']),
            ('trust_id', '!=', False),
        ], limit=1)
        if ods_org and ods_org.trust_id:
            return ods_org.trust_id
        return None

    def _create_trust(self, parsed, ods_org, role_mapping):
        """Create a new NHS trust record dynamically mapping regional fields and relationships."""
        health_system = role_mapping.health_system if role_mapping.health_system != 'both' else 'nhs_england'

        country = self._resolve_country(parsed.get('country', ''))

        active_rels = parsed.get('active_relations', [])
        icb = False
        ics = False
        health_board = False
        welsh_lhb = False

        if health_system == 'nhs_england':
            if active_rels:
                icb = self.env['nhs.icb'].search([('code', 'in', active_rels)], limit=1)
                ics = self.env['nhs.ics'].search([('code', 'in', active_rels)], limit=1)
                if not icb:
                    for code in active_rels:
                        org_name = ""
                        org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                        if org_record:
                            org_name = org_record.name
                        else:
                            try:
                                res = self.api.get_organisation(code)
                                org_name = res.get('Organisation', {}).get('Name', '')
                            except Exception:
                                pass
                        if org_name:
                            clean_name = org_name.upper().replace('INTEGRATED CARE BOARD', '').replace('ICB', '').replace('NHS', '').strip()
                            if clean_name:
                                matched_icb = self.env['nhs.icb'].search([('name', 'ilike', clean_name)], limit=1)
                                if matched_icb:
                                    icb = matched_icb
                                    icb.code = code
                                    break
            if ics and not icb:
                icb = ics.icb_id
        elif health_system == 'nhs_scotland':
            board_codes = [parsed['ods_code']] + active_rels
            health_board = self.env['nhs.health.board'].search([('code', 'in', board_codes)], limit=1)
            if not health_board:
                for code in board_codes:
                    org_name = ""
                    org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                    if org_record:
                        org_name = org_record.name
                    else:
                        try:
                            res = self.api.get_organisation(code)
                            org_name = res.get('Organisation', {}).get('Name', '')
                        except Exception:
                            pass
                    if org_name:
                        clean_name = org_name.upper().replace('HEALTH BOARD', '').replace('NHS', '').strip()
                        if clean_name:
                            matched_board = self.env['nhs.health.board'].search([('name', 'ilike', clean_name)], limit=1)
                            if matched_board:
                                health_board = matched_board
                                health_board.code = code
                                break
        elif health_system == 'nhs_wales':
            lhb_codes = [parsed['ods_code']] + active_rels
            welsh_lhb = self.env['nhs.welsh.lhb'].search([('code', 'in', lhb_codes)], limit=1)
            if not welsh_lhb:
                for code in lhb_codes:
                    org_name = ""
                    org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                    if org_record:
                        org_name = org_record.name
                    else:
                        try:
                            res = self.api.get_organisation(code)
                            org_name = res.get('Organisation', {}).get('Name', '')
                        except Exception:
                            pass
                    if org_name:
                        clean_name = org_name.upper().replace('UNIVERSITY', '').replace('TEACHING', '').replace('LOCAL', '').replace('HEALTH BOARD', '').replace('LHB', '').replace('NHS', '').strip()
                        if clean_name:
                            matched_lhb = self.env['nhs.welsh.lhb'].search([('name', 'ilike', clean_name)], limit=1)
                            if matched_lhb:
                                welsh_lhb = matched_lhb
                                welsh_lhb.code = code
                                break

        # region_id is required=True (NOT NULL in DB) — resolve from health_system
        region = False
        if icb and icb.region_id:
            region = icb.region_id
        elif health_board and health_board.region_id:
            region = health_board.region_id
        elif welsh_lhb and welsh_lhb.region_id:
            region = welsh_lhb.region_id

        if not region:
            region = self.env['nhs.region'].search([('health_system', '=', health_system)], limit=1)

        vals = {
            'name': parsed.get('name', ''),
            'ods_code': parsed['ods_code'],
            'health_system': health_system,
            'street': parsed.get('address_line1'),
            'street2': parsed.get('address_line2'),
            'city': parsed.get('city'),
            'zip': parsed.get('postcode'),
            'phone': parsed.get('phone'),
            'establishment_date': parsed.get('operational_start_date'),
            'state': TRUST_STATUS_MAP.get(parsed.get('status', 'active'), 'active'),
        }
        if region:
            vals['region_id'] = region.id
        if icb:
            vals['icb_id'] = icb.id
        if ics:
            vals['ics_id'] = ics.id
        if health_board:
            vals['health_board_id'] = health_board.id
        if welsh_lhb:
            vals['welsh_lhb_id'] = welsh_lhb.id

        trust_type = role_mapping.trust_type_id or self.env['nhs.trust.type'].search([], limit=1)
        if trust_type:
            vals['trust_type_id'] = trust_type.id
        if country:
            vals['country_id'] = country.id

        # nhs_ods_sync=True bypasses provenance hook and governance constraint check
        ctx = {
            'nhs_ods_sync': True,
            'approved_state_change': True,
            'nhs_ods_sync_run_id': self.run.id,
        }
        trust = self.env['nhs.trust'].with_context(**ctx).sudo().create(vals)
        if ods_org:
            ods_org.trust_id = trust
            trust.with_context(nhs_ods_sync=True).ods_org_id = ods_org
        trust.with_context(nhs_ods_sync=True).ods_last_synced_at = fields.Datetime.now()
        return trust

    def _apply_to_trust(self, parsed, trust, ods_org):
        """Apply parsed values directly to a matched trust record, checking constraints and updating cache references."""
        country = self._resolve_country(parsed.get('country', ''))
        active_rels = parsed.get('active_relations', [])
        icb = False
        ics = False
        health_board = False

        if trust.health_system == 'nhs_england':
            if active_rels:
                icb = self.env['nhs.icb'].search([('code', 'in', active_rels)], limit=1)
                ics = self.env['nhs.ics'].search([('code', 'in', active_rels)], limit=1)
                if not icb:
                    for code in active_rels:
                        org_name = ""
                        org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                        if org_record:
                            org_name = org_record.name
                        else:
                            try:
                                res = self.api.get_organisation(code)
                                org_name = res.get('Organisation', {}).get('Name', '')
                            except Exception:
                                pass
                        if org_name:
                            clean_name = org_name.upper().replace('INTEGRATED CARE BOARD', '').replace('ICB', '').replace('NHS', '').strip()
                            if clean_name:
                                matched_icb = self.env['nhs.icb'].search([('name', 'ilike', clean_name)], limit=1)
                                if matched_icb:
                                    icb = matched_icb
                                    icb.code = code
                                    break
            if ics and not icb:
                icb = ics.icb_id
        elif trust.health_system == 'nhs_scotland':
            board_codes = [parsed['ods_code']] + active_rels
            health_board = self.env['nhs.health.board'].search([('code', 'in', board_codes)], limit=1)
            if not health_board:
                for code in board_codes:
                    org_name = ""
                    org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                    if org_record:
                        org_name = org_record.name
                    else:
                        try:
                            res = self.api.get_organisation(code)
                            org_name = res.get('Organisation', {}).get('Name', '')
                        except Exception:
                            pass
                    if org_name:
                        clean_name = org_name.upper().replace('HEALTH BOARD', '').replace('NHS', '').strip()
                        if clean_name:
                            matched_board = self.env['nhs.health.board'].search([('name', 'ilike', clean_name)], limit=1)
                            if matched_board:
                                health_board = matched_board
                                health_board.code = code
                                break

        vals = {}
        field_map = {
            'name': parsed.get('name'),
            'street': parsed.get('address_line1'),
            'street2': parsed.get('address_line2'),
            'city': parsed.get('city'),
            'zip': parsed.get('postcode'),
            'phone': parsed.get('phone'),
            'establishment_date': parsed.get('operational_start_date'),
        }
        for field, value in field_map.items():
            if value and getattr(trust, field, None) != value:
                vals[field] = value
        if country and trust.country_id != country:
            vals['country_id'] = country.id

        if icb and trust.icb_id != icb:
            vals['icb_id'] = icb.id
            if icb.region_id and trust.region_id != icb.region_id:
                vals['region_id'] = icb.region_id.id
        if ics and trust.ics_id != ics:
            vals['ics_id'] = ics.id
        if health_board and trust.health_board_id != health_board:
            vals['health_board_id'] = health_board.id
            if health_board.region_id and trust.region_id != health_board.region_id:
                vals['region_id'] = health_board.region_id.id

        ods_status = TRUST_STATUS_MAP.get(parsed.get('status', 'active'), 'dissolved')
        if ods_status != trust.state:
            current = trust.state or 'draft'
            allowed = ALLOWED_TRANSITIONS.get(current, [])
            if ods_status in allowed:
                vals['state'] = ods_status

        if not vals:
            return []

        ctx = {'nhs_ods_sync': True, 'approved_state_change': True, 'nhs_ods_sync_run_id': self.run.id}
        trust.with_context(**ctx).write(vals)

        if ods_org and not trust.ods_org_id:
            trust.with_context(nhs_ods_sync=True).ods_org_id = ods_org
        trust.with_context(nhs_ods_sync=True).ods_last_synced_at = fields.Datetime.now()

        return list(vals.keys())

    def _compute_diff(self, parsed, trust):
        """Compare parsed ODS data with current trust fields to produce a diff dictionary."""
        diff = {}
        field_map = {
            'name': parsed.get('name'),
            'street': parsed.get('address_line1'),
            'city': parsed.get('city'),
            'zip': parsed.get('postcode'),
            'phone': parsed.get('phone'),
        }
        for field, ods_val in field_map.items():
            trust_val = getattr(trust, field, None)
            if ods_val and trust_val != ods_val:
                diff[field] = {'current': trust_val, 'ods': ods_val}
        return diff

    def _resolve_country(self, country_text):
        """Resolve an Odoo res.country record from a raw country text string."""
        if not country_text:
            return None
        iso = COUNTRY_MAP.get(country_text.upper())
        if iso:
            country = self.env['res.country'].search([('code', '=', iso)], limit=1)
            return country or None
        country = self.env['res.country'].search([('name', 'ilike', country_text)], limit=1)
        return country or None

    def _record_detail(self, ods_code, outcome, trust=None, ods_org=None,
                       changed_fields=None, error_message=None, skip_reason=None,
                       diff_json=None, duration_ms=0):
        """Create a sync detail record mapping outcomes, errors, or skip reasons."""
        return self.env['nhs.ods.sync.detail'].sudo().create({
            'sync_run_id': self.run.id,
            'ods_code': ods_code,
            'ods_organisation_id': ods_org.id if ods_org else False,
            'outcome': outcome,
            'trust_id': trust.id if trust else False,
            'changed_fields': changed_fields,
            'error_message': error_message,
            'skip_reason': skip_reason,
            'diff_json': diff_json,
            'duration_ms': duration_ms,
        })

    def _record_conflicts(self, conflicts, trust, ods_org, detail):
        """Create conflict records for any detected discrepancies on the trust."""
        for c in conflicts:
            conflict = self.env['nhs.ods.sync.conflict'].sudo().create({
                'sync_run_id': self.run.id,
                'sync_detail_id': detail.id,
                'trust_id': trust.id,
                'ods_organisation_id': ods_org.id,
                'field_name': c.get('field_name', ''),
                'field_label': c.get('field_label', ''),
                'current_value': str(c.get('current_value', '') or ''),

                'ods_value': str(c.get('ods_value', '') or ''),
                'conflict_type': c.get('type', 'field_diff'),
                'state': 'pending',
            })
            self.env['nhs.ods.sync.detail'].browse(detail.id).write({
                'conflict_ids': [(4, conflict.id)],
            })
