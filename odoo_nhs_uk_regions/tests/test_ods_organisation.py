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
from unittest.mock import patch

from odoo.tests.common import tagged

from odoo.addons.odoo_nhs_ods_sync.services.ods_api_client import OdsApiClient

from .common import UkRegionsCommon


def _fake_lhb_payload(ods_code, role_code):
    """Return a minimal Spine ODS payload describing a Welsh LHB."""
    return {
        'Organisation': {
            'OrgId': {'extension': ods_code},
            'Name': 'Some Welsh Health Board',
            'Status': 'Active',
            'Date': [{'Type': 'Operational', 'Start': '2009-10-01'}],
            'Roles': {'Role': [
                {'id': role_code, 'primaryRole': True, 'Status': 'Active'},
            ]},
            'LastChangeDate': '2026-01-01',
        }
    }


@tagged('post_install', '-at_install')
class TestOdsOrganisation(UkRegionsCommon):
    """Cover the nhs.ods.organisation extension that links cached ODS orgs and
    their synced trusts to the matching Welsh LHB."""

    def test_refresh_from_ods_links_welsh_lhb(self):
        """refresh_from_ods links a RO144 org to the LHB sharing its ODS code."""
        org = self.env['nhs.ods.organisation'].create({
            'ods_code': '7A6',  # matches the seeded Aneurin Bevan LHB
            'name': 'Placeholder',
            'status': 'active',
        })
        payload = _fake_lhb_payload('7A6', 'RO144')
        with patch.object(OdsApiClient, 'get_organisation', return_value=payload):
            org.refresh_from_ods()

        self.assertEqual(org.primary_role_code, 'RO144')
        self.assertEqual(org.welsh_lhb_id, self.lhb_aneurin)

    def test_apply_to_trust_resolves_welsh_lhb(self):
        """apply_to_trust caches the LHB on the org and on the created trust."""
        lhb = self.make_welsh_lhb('7A9', 'Apply To Trust LHB')
        # Role mapping so the sync engine classifies the org as NHS Wales.
        self.env['nhs.ods.role.mapping'].create({
            'role_code': 'RO_UKR_TEST',
            'role_name': 'Welsh LHB (test)',
            'trust_type_id': self.type_welsh_uhb.id,
            'health_system': 'nhs_wales',
        })
        org = self.env['nhs.ods.organisation'].create({
            'ods_code': '7A9',  # matches the LHB created above; no seed trust uses it
            'name': 'Apply To Trust Org',
            'status': 'active',
            'primary_role_code': 'RO_UKR_TEST',
            'operational_start_date': '2009-10-01',
        })

        trust = org.apply_to_trust()

        self.assertTrue(trust)
        self.assertEqual(trust.health_system, 'nhs_wales')
        self.assertEqual(trust.welsh_lhb_id, lhb)
        self.assertEqual(org.welsh_lhb_id, lhb)
        self.assertEqual(org.trust_id, trust)
