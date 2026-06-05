# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):

    def test_action_sync_users_new(self):
        """Test syncing a new slack user creates a res.users record successfully"""
        mock_members = [
            {
                'id': 'U12345',
                'real_name': 'Slack Member 1',
                'is_email_confirmed': True,
                'profile': {
                    'email': 'slack_member_1@example.com'
                }
            }
        ]
        
        # Verify user does not exist yet
        user_before = self.env['res.users'].search([('slack_user_ref', '=', 'U12345')])
        self.assertFalse(user_before.exists())
        
        # Run sync
        self.env.user.action_sync_users(mock_members)
        
        # Verify user now exists
        user_after = self.env['res.users'].search([('slack_user_ref', '=', 'U12345')])
        self.assertTrue(user_after.exists())
        self.assertEqual(user_after.name, 'Slack Member 1')
        self.assertEqual(user_after.login, 'slack_member_1@example.com')
        self.assertTrue(user_after.is_slack_internal_users)

    def test_action_sync_users_existing(self):
        """Test syncing existing Slack user updates the record instead of raising error"""
        existing_user = self.env['res.users'].create({
            'name': 'Existing Slack User',
            'login': 'existing_slack@example.com',
            'slack_user_ref': 'U88888',
            'is_slack_internal_users': True,
        })
        
        mock_members = [
            {
                'id': 'U99999',  # New Slack ref
                'real_name': 'Existing Slack User',
                'is_email_confirmed': True,
                'profile': {
                    'email': 'existing_slack@example.com'
                }
            }
        ]
        
        self.env.user.action_sync_users(mock_members)
        
        # Slack user ref should have been updated
        self.assertEqual(existing_user.slack_user_ref, 'U99999')
