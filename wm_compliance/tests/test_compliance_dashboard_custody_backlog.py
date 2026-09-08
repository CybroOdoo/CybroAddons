# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date, timedelta
from odoo.tests.common import tagged, TransactionCase


@tagged('post_install', '-at_install', 'wm_compliance', 'wm_dashboard_custody')
class TestComplianceDashboardCustodyBacklog(TransactionCase):
    """
    Unit tests verifying the Custody and Overdue Backlog calculations
    and data structures displayed on the Compliance Dashboard.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data and fixtures for compliance dashboard backlog testing."""
        super().setUpClass()
        cls.Dashboard = cls.env['wm.compliance.dashboard']
        cls.Manifest = cls.env['wm.compliance.manifest']
        cls.Custody = cls.env['wm.compliance.custody']

        cls.generator = cls.env['res.partner'].create({
            'name': 'Audit Generator Partner',
            'is_generator': True,
        })
        cls.transporter = cls.env['res.partner'].create({
            'name': 'Audit Transporter Partner',
            'is_transporter': True,
        })
        cls.facility = cls.env['wm.disposal.facility'].create({
            'name': 'Audit Disposal Facility',
            'facility_type': 'recycling',
        })
        cls.category = cls.env['wm.waste.category'].create({
            'name': 'Audit Hazardous Waste Category',
            'code': 'AHWC01',
        })

    def test_overdue_and_custody_backlog_figures(self):
        """
        Verify that:
        1. Overdue manifests (>7 days in submitted/collected state) are accurately counted.
        2. Pending custody manifests (submitted/collected with no custody logs) are accurately counted.
        3. Draft and disposed manifests are excluded from the backlog.
        4. The combined urgent_manifests payload for Custody & Overdue Backlog card is correctly formed.
        """
        today = date.today()
        ten_days_ago = today - timedelta(days=10)
        two_days_ago = today - timedelta(days=2)

        # Baseline data
        initial_data = self.Dashboard.get_dashboard_data('month')
        base_overdue = initial_data['overdue_manifest_count']
        base_pending_custody = initial_data['pending_custody_count']

        # 1. Create a manifest that is OVERDUE and has custody log
        manifest_overdue = self.Manifest.create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': ten_days_ago,
            'state': 'submitted',
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 150.0,
            })],
        })
        self.Custody.create({
            'manifest_id': manifest_overdue.id,
            'action': 'generated',
            'location': 'Generator Site',
        })

        # 2. Create a manifest that is RECENT (not overdue) but has NO custody log
        manifest_no_custody = self.Manifest.create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': two_days_ago,
            'state': 'collected',
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 200.0,
            })],
        })

        # 3. Create a manifest that is BOTH overdue AND has NO custody log
        manifest_both = self.Manifest.create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': ten_days_ago,
            'state': 'submitted',
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 300.0,
            })],
        })

        # 4. Create a manifest in DRAFT with old date and no custody (should NOT be counted)
        self.Manifest.create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': ten_days_ago,
            'state': 'draft',
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 50.0,
            })],
        })

        # 5. Create a DISPOSED manifest with old date (should NOT be counted)
        self.Manifest.create({
            'generator_id': self.generator.id,
            'transporter_id': self.transporter.id,
            'disposal_facility_id': self.facility.id,
            'manifest_date': ten_days_ago,
            'state': 'disposed',
            'line_ids': [(0, 0, {
                'waste_category_id': self.category.id,
                'quantity': 500.0,
            })],
        })

        # Query dashboard
        data = self.Dashboard.get_dashboard_data('month')

        # Verify Overdue count (manifest_overdue + manifest_both = +2)
        self.assertEqual(data['overdue_manifest_count'], base_overdue + 2)

        # Verify Pending Custody count (manifest_no_custody + manifest_both = +2)
        self.assertEqual(data['pending_custody_count'], base_pending_custody + 2)

        # Verify urgent_manifests list
        urgent_ids = [m['id'] for m in data['urgent_manifests']]
        self.assertIn(manifest_overdue.id, urgent_ids)
        self.assertIn(manifest_no_custody.id, urgent_ids)
        self.assertIn(manifest_both.id, urgent_ids)

        # Check issues and labels
        overdue_entry = next(m for m in data['urgent_manifests'] if m['id'] == manifest_overdue.id)
        self.assertEqual(overdue_entry['issue'], 'overdue')
        self.assertIn('Overdue', overdue_entry['issue_label'])

        no_custody_entry = next(m for m in data['urgent_manifests'] if m['id'] == manifest_no_custody.id)
        self.assertEqual(no_custody_entry['issue'], 'pending_custody')
        self.assertIn('Custody', no_custody_entry['issue_label'])

        # manifest_both has both issues; it should appear only once (deduplicated)
        both_entries = [m for m in data['urgent_manifests'] if m['id'] == manifest_both.id]
        self.assertEqual(len(both_entries), 1)
        self.assertEqual(both_entries[0]['issue'], 'overdue')  # prioritized as overdue

        # Resolving pending custody by adding a custody log removes it from pending custody count
        self.Custody.create({
            'manifest_id': manifest_no_custody.id,
            'action': 'in_transit',
            'location': 'Hub 1',
        })
        updated_data = self.Dashboard.get_dashboard_data('month')
        self.assertEqual(updated_data['pending_custody_count'], base_pending_custody + 1)
