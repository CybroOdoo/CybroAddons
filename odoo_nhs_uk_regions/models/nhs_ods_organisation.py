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


class NhsOdsOrganisation(models.Model):
    """Extend ODS organisation model to support Welsh LHBs."""
    _inherit = 'nhs.ods.organisation'

    welsh_lhb_id = fields.Many2one(
        'nhs.welsh.lhb',
        string='Linked Welsh LHB',
        ondelete='set null',
        help="If this ODS org is a Welsh Local Health Board (RO144/RO142), links to the nhs.welsh.lhb record."
    )

    def apply_to_trust(self):
        """Extend apply_to_trust to store resolved welsh_lhb_id on the ODS cache record."""
        trust = super(NhsOdsOrganisation, self).apply_to_trust()
        
        # Resolve active relationships for Welsh LHBs
        active_rels = []
        if self.raw_json:
            try:
                import json
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
        
        welsh_lhb = False
        lhb_codes = [self.ods_code] + active_rels
        welsh_lhb = self.env['nhs.welsh.lhb'].search([('code', 'in', lhb_codes)], limit=1)
        if not welsh_lhb:
            from ...odoo_nhs_ods_sync.services.ods_api_client import OdsApiClient
            api_client = OdsApiClient(self.env)
            for code in lhb_codes:
                org_name = ""
                org_record = self.env['nhs.ods.organisation'].search([('ods_code', '=', code)], limit=1)
                if org_record:
                    org_name = org_record.name
                else:
                    try:
                        res = api_client.get_organisation(code)
                        org_name = res.get('Organisation', {}).get('Name', '')
                    except Exception:
                        pass
                if org_name:
                    clean_name = org_name.upper().replace('UNIVERSITY', '').replace('TEACHING', '').replace('LOCAL', '').replace('HEALTH BOARD', '').replace('LHB', '').replace('NHS', '').strip()
                    if clean_name:
                        matched_lhb = self.env['nhs.welsh.lhb'].search([('name', 'ilike', clean_name)], limit=1)
                        if matched_lhb:
                            welsh_lhb = matched_lhb
                            break
        if not welsh_lhb and self.postcode:
            pc = self.postcode.strip().upper()
            outcode = pc.split()[0] if pc else ''
            fallback_trust = self.env['nhs.trust'].search([
                ('zip', '=like', outcode + '%'),
                ('welsh_lhb_id', '!=', False),
            ], limit=1)
            if fallback_trust:
                welsh_lhb = fallback_trust.welsh_lhb_id
            else:
                import re
                match = re.match(r'^[A-Z]{1,2}', outcode)
                if match:
                    area = match.group(0)
                    fallback_trust = self.env['nhs.trust'].search([
                        ('zip', '=like', area + '%'),
                        ('welsh_lhb_id', '!=', False),
                    ], limit=1)
                    if fallback_trust:
                        welsh_lhb = fallback_trust.welsh_lhb_id
        
        if welsh_lhb:
            self.write({'welsh_lhb_id': welsh_lhb.id})
            # Also update the linked trust with the welsh_lhb_id!
            if trust:
                ctx = {'nhs_ods_sync': True, 'approved_state_change': True}
                trust.with_context(**ctx).write({'welsh_lhb_id': welsh_lhb.id})
            
        return trust

    def refresh_from_ods(self):
        """Extend refresh_from_ods to link to Welsh LHB if it's a Welsh LHB organisation."""
        res = super(NhsOdsOrganisation, self).refresh_from_ods()
        if self.primary_role_code in ('RO144', 'RO142'):
            lhb = self.env['nhs.welsh.lhb'].search([('code', '=', self.ods_code)], limit=1)
            if lhb:
                self.write({'welsh_lhb_id': lhb.id})
        return res
