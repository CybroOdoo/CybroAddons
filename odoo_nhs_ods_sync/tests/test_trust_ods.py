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

from .common import OdsSyncCommon


@tagged('post_install', '-at_install')
class TestTrustOds(OdsSyncCommon):
    """Cover the nhs.trust ODS extension: manual provenance tracking, the
    pending-conflict compute, and the provenance action.

    test_manual_create_does_not_crash is a regression guard for the standalone
    bug where the _check_governance_link override called a super() method that
    only exists when odoo_nhs_uk_regions is installed.
    """

    def _manual_trust(self, ods_code, **extra):
        """Create an England trust WITHOUT the sync-context bypass (real user path)."""
        vals = {
            'name': extra.pop('name', 'Manual %s' % ods_code),
            'ods_code': ods_code,
            'health_system': 'nhs_england',
            'trust_type_id': self.type_acute.id,
            'region_id': self.icb_gm.region_id.id,
            'icb_id': self.icb_gm.id,
            'state': 'draft',
        }
        vals.update(extra)
        return self.Trust.create(vals)

    def test_manual_create_does_not_crash_and_records_provenance(self):
        """A manual England trust create succeeds and logs manual provenance."""
        trust = self._manual_trust('MC1')
        self.assertTrue(trust.id)
        prov = self.Provenance.search([
            ('trust_id', '=', trust.id), ('field_name', '=', 'name')])
        self.assertEqual(prov.source, 'manual')

    def test_manual_write_updates_provenance(self):
        """A manual write refreshes provenance for the watched field."""
        trust = self._manual_trust('MC2')
        trust.write({'phone': '0161 000 0000'})
        prov = self.Provenance.search([
            ('trust_id', '=', trust.id), ('field_name', '=', 'phone')])
        self.assertEqual(prov.source, 'manual')

    def test_pending_conflict_count(self):
        """ods_pending_conflict_count counts only pending conflicts on the trust."""
        trust = self._manual_trust('MC3')
        ods_org = self.make_ods_org('MC3')
        run = self.make_run('full')
        detail = self.Detail.create({
            'sync_run_id': run.id, 'ods_code': 'MC3', 'outcome': 'conflict',
            'trust_id': trust.id, 'ods_organisation_id': ods_org.id,
        })
        self.Conflict.create({
            'sync_run_id': run.id, 'sync_detail_id': detail.id, 'trust_id': trust.id,
            'ods_organisation_id': ods_org.id, 'field_name': 'phone', 'state': 'pending',
        })
        trust.invalidate_recordset(['ods_pending_conflict_count'])
        self.assertEqual(trust.ods_pending_conflict_count, 1)

    def test_action_view_provenance(self):
        """action_view_provenance targets provenance rows for this trust."""
        trust = self._manual_trust('MC4')
        action = trust.action_view_provenance()
        self.assertEqual(action['res_model'], 'nhs.ods.field.provenance')
        self.assertIn(('trust_id', '=', trust.id), action['domain'])
