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
from odoo.tests.common import tagged

from odoo.addons.odoo_nhs_ods_sync.services.ods_sync_engine import OdsSyncEngine

from .common import OdsSyncCommon


@tagged('post_install', '-at_install')
class TestSyncEngine(OdsSyncCommon):
    """Cover the OdsSyncEngine units that do not require a live API call:
    code extraction, country resolution, cache upsert, trust match/create/apply,
    and diff computation."""

    def setUp(self):
        super().setUp()
        self.run = self.make_run('full')
        self.engine = OdsSyncEngine(self.env, self.run)

    # ---- pure helpers -------------------------------------------------
    def test_extract_code(self):
        """_extract_code reads OrgId.extension and tolerates malformed stubs."""
        self.assertEqual(self.engine._extract_code({'OrgId': {'extension': 'rw1'}}), 'rw1')
        self.assertEqual(self.engine._extract_code({'no_org': 1}), '')
        self.assertEqual(self.engine._extract_code('not-a-dict'), '')

    def test_resolve_country(self):
        """_resolve_country maps known nations to GB and blanks to None."""
        country = self.engine._resolve_country('England')
        self.assertTrue(country)
        self.assertEqual(country.code, 'GB')
        self.assertIsNone(self.engine._resolve_country(''))

    # ---- cache upsert -------------------------------------------------
    def test_upsert_cache_creates_then_updates(self):
        """_upsert_cache creates a cache row, then updates the same row by code."""
        parsed = {'ods_code': 'ZZ1', 'name': 'Cache Org', 'status': 'active',
                  'all_role_codes': ['RO197']}
        org1 = self.engine._upsert_cache(parsed, {'raw': 1})
        self.assertEqual(org1.ods_code, 'ZZ1')
        parsed['name'] = 'Cache Org Renamed'
        org2 = self.engine._upsert_cache(parsed, {'raw': 2})
        self.assertEqual(org1, org2)
        self.assertEqual(self.OdsOrg.search_count([('ods_code', '=', 'ZZ1')]), 1)

    # ---- match / create / apply --------------------------------------
    def test_match_trust_by_ods_code(self):
        """_match_trust finds an existing trust by its ODS code."""
        trust = self.make_england_trust('ZZ2')
        self.assertEqual(self.engine._match_trust({'ods_code': 'ZZ2'}), trust)
        self.assertFalse(self.engine._match_trust({'ods_code': 'NOPE'}))

    def test_create_trust_england(self):
        """_create_trust builds an England trust, resolves region, and links cache."""
        ods_org = self.make_ods_org('ZZ3')
        parsed = {'ods_code': 'ZZ3', 'name': 'Created Via Engine', 'status': 'active',
                  'active_relations': [], 'country': 'England'}
        trust = self.engine._create_trust(parsed, ods_org, self.role_ro197)
        self.assertEqual(trust.ods_code, 'ZZ3')
        self.assertEqual(trust.health_system, 'nhs_england')
        self.assertEqual(trust.trust_type_id, self.type_acute)
        self.assertEqual(trust.region_id.health_system, 'nhs_england')
        self.assertEqual(ods_org.trust_id, trust)
        self.assertEqual(trust.ods_org_id, ods_org)

    def test_apply_to_trust_updates_changed_field(self):
        """_apply_to_trust writes only changed fields and reports them; no-op returns []."""
        trust = self.make_england_trust('ZZ4', phone='OLD')
        ods_org = self.make_ods_org('ZZ4')
        parsed = self.parsed_for(trust, phone='NEW')
        changed = self.engine._apply_to_trust(parsed, trust, ods_org)
        self.assertIn('phone', changed)
        self.assertEqual(trust.phone, 'NEW')
        # Re-applying the same data changes nothing.
        self.assertEqual(self.engine._apply_to_trust(self.parsed_for(trust), trust, ods_org), [])

    def test_compute_diff(self):
        """_compute_diff reports current vs ODS values for dry-run previews."""
        trust = self.make_england_trust('ZZ5', phone='OLD')
        diff = self.engine._compute_diff(self.parsed_for(trust, phone='NEW'), trust)
        self.assertIn('phone', diff)
        self.assertEqual(diff['phone'], {'current': 'OLD', 'ods': 'NEW'})
