# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import patch
from odoo.tests.common import TransactionCase

class TestLoginRestriction(TransactionCase):
    """Test cases for login restriction functionality."""

    def setUp(self):
        super(TestLoginRestriction, self).setUp()
        # Create test user
        self.test_user = self.env['res.users'].create({
            'name': 'Test User',
            'login': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
        })
        # Create login restriction config
        self.restriction = self.env['login.restriction.config'].create({
            'user_id': self.test_user.id,
            'is_restricted': True,
            'monday_from': 9.0,
            'monday_to': 17.0,
            'tuesday_from': 9.0,
            'tuesday_to': 17.0,
            'wednesday_from': 9.0,
            'wednesday_to': 17.0,
            'thursday_from': 9.0,
            'thursday_to': 17.0,
            'friday_from': 9.0,
            'friday_to': 17.0,
            'allow_admin_bypass': True,
            'error_message': 'You can only login during working hours (9 AM - 5 PM)',
        })

    def test_restriction_config_creation(self):
        """Test that restriction config is created correctly."""
        self.assertTrue(self.restriction.is_restricted)
        self.assertEqual(self.restriction.user_id.id, self.test_user.id)
        self.assertEqual(self.restriction.monday_from, 9.0)
        self.assertEqual(self.restriction.monday_to, 17.0)

    def test_get_working_hours_monday(self):
        """Test getting working hours for Monday."""
        from_hour, to_hour = self.restriction.get_working_hours(0)
        self.assertEqual(from_hour, 9.0)
        self.assertEqual(to_hour, 17.0)

    def test_get_working_hours_saturday(self):
        """Test getting working hours for Saturday (not set)."""
        from_hour, to_hour = self.restriction.get_working_hours(5)
        self.assertIsNone(from_hour)
        self.assertIsNone(to_hour)

    def test_is_within_working_hours_disabled(self):
        """Test that disabled restrictions always return True."""
        self.restriction.is_restricted = False
        result = self.restriction.is_within_working_hours()
        self.assertTrue(result)

    def test_unique_user_restriction(self):
        """Test that only one restriction config per user is allowed."""
        with self.assertRaises(Exception):
            # Try to create another restriction for same user
            self.env['login.restriction.config'].create({
                'user_id': self.test_user.id,
                'is_restricted': True,
                'monday_from': 8.0,
                'monday_to': 18.0,
            })

    def test_user_check_login_restrictions_enabled(self):
        """Test login restriction check for enabled restriction."""
        self.test_user.check_login_restrictions()  # Should not raise

    def test_user_check_login_restrictions_disabled(self):
        """Test login restriction check for disabled restriction."""
        self.restriction.is_restricted = False
        self.test_user.check_login_restrictions()  # Should not raise

    def test_admin_bypass_allowed(self):
        """Test that admin users can bypass restrictions."""
        # Add user to admin group
        self.test_user.groups_id += self.env.ref('base.group_system')
        self.restriction.allow_admin_bypass = True
        
        # Should not raise even if outside working hours
        self.test_user.check_login_restrictions()

    def test_user_restriction_one2many(self):
        """Test One2Many relationship between user and restrictions."""
        self.assertEqual(len(self.test_user.login_restriction_id), 1)
        self.assertEqual(
            self.test_user.login_restriction_id[0].id, 
            self.restriction.id
        )

    def test_error_message_custom(self):
        """Test that custom error message is stored."""
        custom_message = 'Custom restriction message'
        self.restriction.error_message = custom_message
        self.assertEqual(self.restriction.error_message, custom_message)

    def test_partial_working_hours(self):
        """Test partial working hours (e.g., 9:30 AM to 5:30 PM)."""
        self.restriction.write({
            'monday_from': 9.30,
            'monday_to': 17.30,
        })
        
        # Test 9:25 AM (should be restricted)
        with patch('odoo.addons.auth_login_scheduled_restriction.models.login_restriction_config.datetime') as mock_dt:
            from datetime import datetime
            # Setup mock to return a Monday at 9:25 AM (2023-10-02 is Monday)
            mock_dt.now.return_value = datetime(2023, 10, 2, 9, 25, 0)
            self.assertFalse(self.restriction.is_within_working_hours())
            
        # Test 9:35 AM (should be allowed)
        with patch('odoo.addons.auth_login_scheduled_restriction.models.login_restriction_config.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2023, 10, 2, 9, 35, 0)
            self.assertTrue(self.restriction.is_within_working_hours())

        # Test 5:20 PM (should be allowed)
        with patch('odoo.addons.auth_login_scheduled_restriction.models.login_restriction_config.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2023, 10, 2, 17, 20, 0)
            self.assertTrue(self.restriction.is_within_working_hours())

        # Test 5:40 PM (should be restricted)
        with patch('odoo.addons.auth_login_scheduled_restriction.models.login_restriction_config.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2023, 10, 2, 17, 40, 0)
            self.assertFalse(self.restriction.is_within_working_hours())
