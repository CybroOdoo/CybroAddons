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

from odoo.addons.odoo_nhs_ods_sync.services.ods_conflict_detector import OdsConflictDetector

from .common import OdsSyncCommon


@tagged('post_install', '-at_install')
class TestConflictDetector(OdsSyncCommon):
    """Cover OdsConflictDetector.detect across its four conflict types plus the
    clean (no-conflict) case."""

    def setUp(self):
        super().setUp()
        self.detector = OdsConflictDetector(self.env)

    def _provenance(self, trust, field_name, source='manual', auto_update=True):
        return self.Provenance.create({
            'trust_id': trust.id, 'field_name': field_name,
            'source': source, 'auto_update': auto_update,
        })

    def test_no_conflict_when_matching(self):
        """Identical ODS data with no provenance yields zero conflicts."""
        trust = self.make_england_trust('CD1', phone='123')
        self.assertEqual(self.detector.detect(self.parsed_for(trust), trust, None), [])

    def test_disallowed_state_change(self):
        """An ODS 'inactive' (→dissolved) on a draft trust is a disallowed change."""
        trust = self.make_england_trust('CD2', state='draft')
        parsed = self.parsed_for(trust, status='inactive')
        conflicts = self.detector.detect(parsed, trust, None)
        self.assertEqual([c['type'] for c in conflicts], ['disallowed_state_change'])

    def test_field_diff_on_manual_value(self):
        """A differing field with manual provenance is flagged as a manual-edit conflict."""
        trust = self.make_england_trust('CD3', phone='OLD')
        self._provenance(trust, 'phone', source='manual')
        conflicts = self.detector.detect(self.parsed_for(trust, phone='NEW'), trust, None)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'field_diff')
        self.assertEqual(conflicts[0]['field_name'], 'phone')

    def test_auto_update_disabled(self):
        """A differing field whose provenance has auto_update=False is flagged."""
        trust = self.make_england_trust('CD4', phone='OLD')
        self._provenance(trust, 'phone', source='ods', auto_update=False)
        conflicts = self.detector.detect(self.parsed_for(trust, phone='NEW'), trust, None)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'auto_update_disabled')

    def test_role_demotion(self):
        """A role mapping pointing at a different trust type raises a role change."""
        trust = self.make_england_trust('CD5')  # type = acute
        parsed = self.parsed_for(trust, primary_role_code='RO242')  # mapping -> mental
        conflicts = self.detector.detect(parsed, trust, None)
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'role_demotion')
        self.assertEqual(conflicts[0]['field_name'], 'trust_type_id')
