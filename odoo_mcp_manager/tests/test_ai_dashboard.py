# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestAiDashboard(TransactionCase):

    def setUp(self):
        super(TestAiDashboard, self).setUp()
        self.dashboard = self.env['ai.dashboard'].create({})

    def test_01_compute_counts(self):
        """Test that dashboard counters are populated."""
        # Create at least one provider to see it in counts
        self.env['ai.provider'].create({'name': 'Dash Provider', 'service': 'openai'})
        self.dashboard._compute_counts()
        self.assertGreaterEqual(self.dashboard.provider_count, 1)

    def test_02_get_dashboard_data(self):
        """Test the JSON-RPC data endpoint."""
        data = self.env['ai.dashboard'].get_dashboard_data()
        self.assertEqual(data['status'], 'active')
        self.assertIn('providers', data)
        self.assertIn('tools', data)
        self.assertIn('stats', data)
        self.assertIsInstance(data['activity'], list)

    def test_03_action_open_dashboard(self):
        """Test singleton creation and action return."""
        # Unlink existing to test creation
        self.env['ai.dashboard'].search([]).unlink()
        action = self.env['ai.dashboard'].action_open_dashboard()
        self.assertEqual(action['res_model'], 'ai.dashboard')
        self.assertTrue(action['res_id'])
        # Verify it created a singleton
        self.assertEqual(self.env['ai.dashboard'].search_count([]), 1)
