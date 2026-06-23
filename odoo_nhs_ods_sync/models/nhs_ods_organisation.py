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

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class NhsOdsOrganisation(models.Model):
    """Store cached ODS API payloads and parse organization data for Odoo models."""
    _name = 'nhs.ods.organisation'
    _inherit = ['mail.thread']
    _description = 'Cached ODS API payload for a single organisation'
    _order = 'ods_code'
    _rec_name = 'display_name'

    ods_code = fields.Char(
        string='ODS Code',
        required=True,
        index=True,
        help="The OrgId.extension from the ODS payload. Unique. Uppercase enforced.",
    )
    name = fields.Char(
        string='Name',
        required=True,
        help="Organisation.Name from the ODS payload. Title-cased on store.",
    )
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', required=True, default='active',
        help="Mirrors ODS Organisation.Status.",
    )
    primary_role_code = fields.Char(
        string='Primary Role Code',
        index=True,
        help="Role code (e.g. RO197) of the primary role.",
    )
    non_primary_role_codes = fields.Char(
        string='Non-Primary Role Codes',
        help="Comma-separated list of non-primary role codes.",
    )
    operational_start_date = fields.Date(
        string='Operational Start Date',
        help="Date[Type=Operational].Start — maps to nhs.trust.establishment_date.",
    )
    operational_end_date = fields.Date(
        string='Operational End Date',
        help="Date[Type=Operational].End — present when an organisation has been wound up.",
    )
    address_line1 = fields.Char(string='Address Line 1', help="Parsed street address line 1.")
    address_line2 = fields.Char(string='Address Line 2', help="Parsed street address line 2.")
    city = fields.Char(string='Town / City', help="Parsed town or city name.")
    county = fields.Char(string='County', help="Parsed county name.")
    postcode = fields.Char(string='Postcode', help="Parsed postcode.")
    country_text = fields.Char(
        string='Country (ODS)',
        help="GeoLoc.Location.Country text value. Used to resolve country_id.",
    )
    phone = fields.Char(
        string='Phone',
        help="First tel contact from the ODS payload.",
    )
    email = fields.Char(
        string='Email',
        help="First email/mailto contact from the ODS payload.",
    )
    website = fields.Char(
        string='Website',
        help="First http/https website contact from the ODS payload.",
    )
    last_change_date = fields.Date(
        string='ODS Last Change Date',
        help="ODS LastChangeDate. Used for delta sync.",
    )
    raw_json = fields.Text(
        string='Raw JSON',
        help="Full ODS payload stored verbatim for replay.",
    )
    raw_payload_hash = fields.Char(
        string='Payload Hash',
        help="SHA-256 of canonicalised JSON. Used to short-circuit unchanged payloads.",
    )
    last_fetched_at = fields.Datetime(
        string='Last Fetched At',
        required=True,
        default=fields.Datetime.now,
        help="When this cache entry was last refreshed from the ODS API.",
    )
    trust_id = fields.Many2one(
        'nhs.trust',
        string='Linked Trust',
        ondelete='set null',
        help="The corresponding nhs.trust record matched by ods_code.",
    )
    icb_id = fields.Many2one(
        'nhs.icb',
        string='Linked ICB',
        ondelete='set null',
        help="If this ODS org is an ICB (RO165), links to the nhs.icb record.",
    )
    health_board_id = fields.Many2one(
        'nhs.health.board',
        string='Linked Health Board',
        ondelete='set null',
        help="If this ODS org is a Scottish board (RO140), links to nhs.health.board.",
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Format '[ODS_CODE] Name'.",
    )
    sync_run_ids = fields.One2many(
        'nhs.ods.sync.detail',
        'ods_organisation_id',
        string='Sync Details',
        help="All sync details that have touched this org.",
    )

    _ods_code_uniq = models.Constraint('unique(ods_code)', 'Each ODS code must be unique in the cache.')

    @api.depends('ods_code', 'name')
    def _compute_display_name(self):
        """Compute display name formatting for the organisation."""
        for rec in self:
            if rec.ods_code and rec.name:
                rec.display_name = f'[{rec.ods_code}] {rec.name}'
            else:
                rec.display_name = rec.name or rec.ods_code or ''

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to normalize code and casing on store."""
        for vals in vals_list:
            if vals.get('ods_code'):
                vals['ods_code'] = vals['ods_code'].upper()
            if vals.get('name') and vals['name'].isupper():
                vals['name'] = vals['name'].title()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to normalize code and casing on store."""
        if vals.get('ods_code'):
            vals['ods_code'] = vals['ods_code'].upper()
        if vals.get('name') and vals['name'].isupper():
            vals['name'] = vals['name'].title()
        return super().write(vals)


    def refresh_from_ods(self):
        """Fetch latest organisation details from Spine API and refresh cache."""
        self.ensure_one()
        from ..services.ods_api_client import OdsApiClient

        from ..services.ods_payload_parser import parse_ods_payload
        client = OdsApiClient(self.env)
        raw = client.get_organisation(self.ods_code)
        org_data = raw.get('Organisation', raw)
        parsed = parse_ods_payload(org_data)
        write_vals = {
            'name': parsed.get('name', self.name),
            'status': parsed.get('status', self.status),
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
            'email': parsed.get('email'),
            'website': parsed.get('website'),
            'last_change_date': parsed.get('last_changed_at'),
            'raw_json': json.dumps(org_data),
            'raw_payload_hash': parsed.get('raw_payload_hash'),
            'last_fetched_at': fields.Datetime.now(),
        }
        if parsed.get('primary_role_code') == 'RO165':
            write_vals['icb_id'] = self.env['nhs.icb'].search([('code', '=', self.ods_code)], limit=1).id
        elif parsed.get('primary_role_code') == 'RO140':
            write_vals['health_board_id'] = self.env['nhs.health.board'].search([('code', '=', self.ods_code)], limit=1).id

        self.write(write_vals)
        return self

    def action_refresh_and_apply(self):
        """Refresh from ODS API then create or update the linked nhs.trust."""
        self.ensure_one()
        self.refresh_from_ods()
        trust = self.apply_to_trust()
        msg = (f'{self.ods_code} refreshed and trust "{trust.name}" updated.'
               if trust else f'{self.ods_code} refreshed from ODS API.')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'ODS Refresh Complete',
                'message': msg,
                'type': 'success',
                'sticky': False,
            },
        }

    def apply_to_trust(self):
        """Create or update linked trust record based on parsed cache values."""
        self.ensure_one()
        country = self.env['res.country'].search([('name', 'ilike', self.country_text)], limit=1)


        # Resolve health_system and trust_type from role mapping
        role_mapping = self.env['nhs.ods.role.mapping'].search([
            ('role_code', '=', self.primary_role_code),
            ('active', '=', True),
        ], limit=1)
        health_system = 'nhs_england'
        trust_type_id = False
        if role_mapping:
            health_system = (role_mapping.health_system
                             if role_mapping.health_system != 'both' else 'nhs_england')
            trust_type_id = role_mapping.trust_type_id.id if role_mapping.trust_type_id else False
        if not trust_type_id:
            fallback_type = self.env['nhs.trust.type'].search([], limit=1)
            trust_type_id = fallback_type.id if fallback_type else False

        # Parse active relationships from raw_json
        active_rels = []
        if self.raw_json:
            try:
                raw_data = json.loads(self.raw_json)
                rels = raw_data.get('Rels', {}).get('Rel', [])
                if not isinstance(rels, list):
                    rels = [rels]
                for rel in rels:
                    if isinstance(rel, dict) and rel.get('Status') == 'Active':
                        target = rel.get('Target', {})
                        if isinstance(target, dict):
                            target_org = target.get('OrgId', {})
                            if isinstance(target_org, dict):
                                target_code = target_org.get('extension')
                                if target_code:
                                    active_rels.append(target_code.upper())
            except Exception:
                pass

        icb = False
        ics = False
        health_board = False
        welsh_lhb = False
        region = False

        if health_system == 'nhs_england':
            if active_rels:
                icb = self.env['nhs.icb'].search([('code', 'in', active_rels)], limit=1)
                ics = self.env['nhs.ics'].search([('code', 'in', active_rels)], limit=1)
                if not icb:
                    from ..services.ods_api_client import OdsApiClient
                    api = OdsApiClient(self.env)
                    for code in active_rels:
                        org_name = ""
                        org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                        if org_record:
                            org_name = org_record.name
                        else:
                            try:
                                res = api.get_organisation(code)
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

            # Try postcodes.io API lookup first
            if not icb and self.postcode:
                pc = self.postcode.strip().replace(' ', '').upper()
                try:
                    import urllib.request
                    import json
                    url = f'https://api.postcodes.io/postcodes/{pc}'
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=2) as response:
                        res_data = json.loads(response.read().decode())
                        result = res_data.get('result', {})
                        api_icb_name = result.get('icb')
                        if api_icb_name:
                            clean_name = api_icb_name.upper().replace('INTEGRATED CARE BOARD', '').replace('ICB', '').replace('NHS', '').strip()
                            matched_icb = self.env['nhs.icb'].search([('name', 'ilike', clean_name)], limit=1)
                            if matched_icb:
                                icb = matched_icb
                        
                        api_region_name = result.get('nhs_region')
                        if api_region_name:
                            matched_region = self.env['nhs.region'].search([
                                ('name', 'ilike', api_region_name),
                                ('health_system', '=', 'nhs_england')
                            ], limit=1)
                            if matched_region:
                                region = matched_region
                except Exception:
                    pass

            # Fallback to local database postcode prefix lookup if API lookup failed
            if not icb and self.postcode:
                pc = self.postcode.strip().upper()
                outcode = pc.split()[0] if pc else ''
                fallback_trust = self.env['nhs.trust'].search([
                    ('zip', '=like', outcode + '%'),
                    ('icb_id', '!=', False),
                ], limit=1)
                if fallback_trust:
                    icb = fallback_trust.icb_id
                else:
                    import re
                    match = re.match(r'^[A-Z]{1,2}', outcode)
                    if match:
                        area = match.group(0)
                        fallback_trust = self.env['nhs.trust'].search([
                            ('zip', '=like', area + '%'),
                            ('icb_id', '!=', False),
                        ], limit=1)
                        if fallback_trust:
                            icb = fallback_trust.icb_id
        elif health_system == 'nhs_scotland':
            board_codes = [self.ods_code] + active_rels
            health_board = self.env['nhs.health.board'].search([('code', 'in', board_codes)], limit=1)
            if not health_board:
                from ..services.ods_api_client import OdsApiClient
                api = OdsApiClient(self.env)
                for code in board_codes:
                    org_name = ""
                    org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                    if org_record:
                        org_name = org_record.name
                    else:
                        try:
                            res = api.get_organisation(code)
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
            if not health_board and self.postcode:
                pc = self.postcode.strip().upper()
                outcode = pc.split()[0] if pc else ''
                fallback_trust = self.env['nhs.trust'].search([
                    ('zip', '=like', outcode + '%'),
                    ('health_board_id', '!=', False),
                ], limit=1)
                if fallback_trust:
                    health_board = fallback_trust.health_board_id
                else:
                    import re
                    match = re.match(r'^[A-Z]{1,2}', outcode)
                    if match:
                        area = match.group(0)
                        fallback_trust = self.env['nhs.trust'].search([
                            ('zip', '=like', area + '%'),
                            ('health_board_id', '!=', False),
                        ], limit=1)
                        if fallback_trust:
                            health_board = fallback_trust.health_board_id
        elif health_system == 'nhs_wales':
            lhb_codes = [self.ods_code] + active_rels
            welsh_lhb = self.env['nhs.welsh.lhb'].search([('code', 'in', lhb_codes)], limit=1)
            if not welsh_lhb:
                from ..services.ods_api_client import OdsApiClient
                api = OdsApiClient(self.env)
                for code in lhb_codes:
                    org_name = ""
                    org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                    if org_record:
                        org_name = org_record.name
                    else:
                        try:
                            res = api.get_organisation(code)
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

        if not region:
            if icb and icb.region_id:
                region = icb.region_id
            elif health_board and health_board.region_id:
                region = health_board.region_id
            elif welsh_lhb and welsh_lhb.region_id:
                region = welsh_lhb.region_id

        if not region:
            region = self.env['nhs.region'].search(
                [('health_system', '=', health_system)], limit=1)

        vals = {
            'name': self.name,
            'ods_code': self.ods_code,
            'health_system': health_system,
            'establishment_date': self.operational_start_date,
            'street': self.address_line1,
            'street2': self.address_line2,
            'city': self.city,
            'zip': self.postcode,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'state': 'active' if self.status == 'active' else 'dissolved',
        }
        if region:
            vals['region_id'] = region.id
        if trust_type_id:
            vals['trust_type_id'] = trust_type_id
        if country:
            vals['country_id'] = country.id

        # Set resolved geographic entities
        if icb:
            vals['icb_id'] = icb.id
        if ics:
            vals['ics_id'] = ics.id
        if health_board:
            vals['health_board_id'] = health_board.id
        if welsh_lhb:
            vals['welsh_lhb_id'] = welsh_lhb.id

        ctx = {'nhs_ods_sync': True, 'approved_state_change': True}
        trust_env = self.env['nhs.trust'].with_context(**ctx).sudo()

        if self.trust_id:
            self.trust_id.with_context(**ctx).write(vals)
            self.write({
                'icb_id': icb.id if icb else False,
                'health_board_id': health_board.id if health_board else False,
            })
            return self.trust_id
        else:
            # Check if a trust with this ODS code already exists
            existing = self.env['nhs.trust'].search(
                [('ods_code', '=', self.ods_code)], limit=1)
            if existing:
                existing.with_context(**ctx).write(vals)
                self.trust_id = existing
                self.write({
                    'icb_id': icb.id if icb else False,
                    'health_board_id': health_board.id if health_board else False,
                })
                return existing
            trust = trust_env.create(vals)
            self.trust_id = trust
            self.write({
                'icb_id': icb.id if icb else False,
                'health_board_id': health_board.id if health_board else False,
            })
            return trust

    def detect_conflicts(self):
        """Detect conflicts between ODS cache values and local trust values."""
        self.ensure_one()
        if not self.trust_id:

            return []
        from ..services.ods_conflict_detector import OdsConflictDetector
        import json as _json
        from ..services.ods_payload_parser import parse_ods_payload
        raw_data = _json.loads(self.raw_json) if self.raw_json else {}
        parsed = parse_ods_payload(raw_data)
        detector = OdsConflictDetector(self.env)
        return detector.detect(parsed, self.trust_id, self)
