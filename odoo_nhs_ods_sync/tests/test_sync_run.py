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
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from odoo.addons.odoo_nhs_ods_sync.services.ods_api_client import OdsApiClient

from .common import OdsSyncCommon


def _england_payload(ods_code, role_code='RO197'):
    """Minimal Spine payload (wrapped in 'Organisation') for an England trust."""
    return {'Organisation': {
        'OrgId': {'extension': ods_code},
        'Name': 'Engine Sync Trust',
        'Status': 'Active',
        'Date': [{'Type': 'Operational', 'Start': '2001-01-01'}],
        'GeoLoc': {'Location': {'AddrLn1': '1 Test St', 'Town': 'London',
                                'PostCode': 'E1 1AA', 'Country': 'ENGLAND'}},
        'Contacts': {'Contact': [{'type': 'tel', 'value': '01234'}]},
        'Roles': {'Role': [{'id': role_code, 'primaryRole': True, 'Status': 'Active'}]},
        'LastChangeDate': '2026-02-02',
    }}


@tagged('post_install', '-at_install')
class TestSyncRun(OdsSyncCommon):
    """Cover the nhs.ods.sync.run model: sequencing, computes, run-state guards,
    and an end-to-end targeted run with the API boundary mocked."""

    def test_create_assigns_sequence(self):
        """create() replaces the 'New' placeholder with a SYNC/ sequence value."""
        run = self.make_run('full')
        self.assertNotEqual(run.name, 'New')
        self.assertTrue(run.name.startswith('SYNC/'))

    def test_compute_duration(self):
        """duration is the gap (minutes) between started_at and completed_at."""
        run = self.make_run('full')
        start = datetime(2026, 1, 1, 10, 0, 0)
        run.write({'started_at': start, 'completed_at': start + timedelta(minutes=30)})
        self.assertAlmostEqual(run.duration, 30.0, places=2)

    def test_display_name_includes_reference_and_state(self):
        """display_name combines the reference with type and state labels."""
        run = self.make_run('full')
        self.assertIn(run.name, run.display_name)
        self.assertIn('Full Sync', run.display_name)

    def test_action_run_rejects_non_pending(self):
        """Only pending runs may be started."""
        run = self.make_run('full')
        run.state = 'success'
        with self.assertRaises(UserError):
            run.action_run()

    def test_action_cancel_pending(self):
        """Cancelling a pending run flags it and moves it to cancelled."""
        run = self.make_run('full')
        run.action_cancel()
        self.assertTrue(run.cancel_requested)
        self.assertEqual(run.state, 'cancelled')

    def test_targeted_run_creates_trust_end_to_end(self):
        """A targeted run fetches (mocked), parses, caches, and creates a trust."""
        run = self.make_run('targeted', targeted_ods_code='ZZ7')
        with patch.object(OdsApiClient, 'get_organisation',
                          return_value=_england_payload('ZZ7')):
            run.action_run()

        self.assertEqual(run.state, 'success')
        self.assertEqual(run.created_count, 1)
        trust = self.Trust.search([('ods_code', '=', 'ZZ7')])
        self.assertEqual(len(trust), 1)
        self.assertEqual(trust.health_system, 'nhs_england')
        detail = self.Detail.search([('sync_run_id', '=', run.id), ('outcome', '=', 'created')])
        self.assertEqual(len(detail), 1)
        self.assertEqual(detail.trust_id, trust)

    def test_targeted_run_skips_reference_only_role(self):
        """An RO165 (creates_trust=False) org is cached and skipped, not created."""
        run = self.make_run('targeted', targeted_ods_code='ZZ6')
        with patch.object(OdsApiClient, 'get_organisation',
                          return_value=_england_payload('ZZ6', role_code='RO165')):
            run.action_run()

        self.assertEqual(run.state, 'success')
        self.assertEqual(run.created_count, 0)
        self.assertFalse(self.Trust.search([('ods_code', '=', 'ZZ6')]))
        detail = self.Detail.search([('sync_run_id', '=', run.id)])
        self.assertEqual(detail.outcome, 'skipped')
