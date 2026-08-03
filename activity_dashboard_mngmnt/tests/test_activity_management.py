# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase
from odoo.fields import Date
from datetime import timedelta

class TestActivityManagement(TransactionCase):

    def setUp(self):
        super(TestActivityManagement, self).setUp()
        self.Partner = self.env['res.partner']
        self.Activity = self.env['mail.activity']
        self.Tag = self.env['activity.tag']
        self.ActivityType = self.env['mail.activity.type']
        
        # Use an existing partner to avoid custom constraints (like autopost_bills)
        self.partner = self.Partner.search([], limit=1)
        if not self.partner:
            # Fallback for empty databases (rare in Odoo tests)
            self.partner = self.Partner.create({'name': 'Test Partner'})

        self.activity_type = self.ActivityType.create({
            'name': 'Test Activity Type',
            'category': 'default',
        })
        self.tag = self.Tag.create({'name': 'Test Tag', 'color': 1})

    def test_activity_lifecycle(self):
        """Test the lifecycle of an activity with the dashboard management module."""
        future_date = Date.today() + timedelta(days=5)
        activity = self.Activity.create({
            'activity_type_id': self.activity_type.id,
            'note': 'Test Planned Activity',
            'res_id': self.partner.id,
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'date_deadline': future_date,
            'activity_tag_ids': [(4, self.tag.id)],
        })
        self.assertEqual(activity.state, 'planned', "Activity should be in 'planned' state.")
        self.assertIn(self.tag, activity.activity_tag_ids, "Tag should be assigned to the activity.")

        # 2. Test today activity
        activity.date_deadline = Date.today()
        # Trigger recompute
        activity._compute_state()
        self.assertEqual(activity.state, 'today', "Activity should be in 'today' state.")

        # 3. Test overdue activity
        past_date = Date.today() - timedelta(days=1)
        activity.date_deadline = past_date
        activity._compute_state()
        self.assertEqual(activity.state, 'overdue', "Activity should be in 'overdue' state.")

        # 4. Mark as done and verify it is archived instead of deleted
        activity.action_done()
        
        # In standard Odoo, activity would be unlinked. 
        # In this module, it should exist with active=False and state='done'.
        self.assertTrue(activity.exists(), "Activity should still exist after being marked as done.")
        self.assertFalse(activity.active, "Activity should be archived (active=False) after completion.")
        self.assertEqual(activity.state, 'done', "Activity state should be 'done'.")

    def test_get_activity_method(self):
        """Test the get_activity RPC helper method used by the dashboard."""
        activity = self.Activity.create({
            'activity_type_id': self.activity_type.id,
            'res_id': self.partner.id,
            'res_model_id': self.env['ir.model']._get_id('res.partner'),
            'date_deadline': Date.today(),
        })
        
        result = self.Activity.get_activity(activity.id)
        self.assertEqual(result['model'], 'res.partner')
        self.assertEqual(result['res_id'], self.partner.id)
