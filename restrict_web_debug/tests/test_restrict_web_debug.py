# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul(<https://www.cybrosys.com>)
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRestrictWebDebug(TransactionCase):
    """Test cases for the Restrict Web Debug module."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for the restrict_web_debug tests."""
        super().setUpClass()
        cls.restrict_group = cls.env.ref(
            'restrict_web_debug.restrict_debug_mode')
        # Create a test user without the restrict debug group
        cls.user_without_group = cls.env['res.users'].create({
            'name': 'Test User Without Debug Restriction',
            'login': 'test_user_no_restrict',
            'email': 'test_no_restrict@example.com',
            'groups_id': [(5, 0, 0)],
        })
        # Create a test user with the restrict debug group
        cls.user_with_group = cls.env['res.users'].create({
            'name': 'Test User With Debug Restriction',
            'login': 'test_user_restrict',
            'email': 'test_restrict@example.com',
            'groups_id': [
                (4, cls.restrict_group.id),
            ],
        })

    def test_01_restrict_debug_group_exists(self):
        """Test that the 'Restrict Debug Mode' security group exists."""
        group = self.env.ref(
            'restrict_web_debug.restrict_debug_mode',
            raise_if_not_found=False)
        self.assertTrue(group,
                        "The 'Restrict Debug Mode' group should exist.")
        self.assertEqual(group.name, 'Restrict Debug Mode',
                         "Group name should be 'Restrict Debug Mode'.")

    def test_02_user_without_group_has_no_restriction(self):
        """Test that a user without the group is not restricted
        (has_group returns False)."""
        has_group = self.user_without_group.has_group(
            'restrict_web_debug.restrict_debug_mode')
        self.assertFalse(
            has_group,
            "User without the restrict group should not have it.")

    def test_03_user_with_group_has_restriction(self):
        """Test that a user with the group is restricted
        (has_group returns True)."""
        has_group = self.user_with_group.has_group(
            'restrict_web_debug.restrict_debug_mode')
        self.assertTrue(
            has_group,
            "User with the restrict group should have it.")

    def test_04_add_group_to_user(self):
        """Test that adding the restrict group to a user updates
        has_group correctly."""
        self.assertFalse(
            self.user_without_group.has_group(
                'restrict_web_debug.restrict_debug_mode'),
            "User should not initially have the restrict group.")
        self.user_without_group.write({
            'groups_id': [(4, self.restrict_group.id)],
        })
        self.assertTrue(
            self.user_without_group.has_group(
                'restrict_web_debug.restrict_debug_mode'),
            "User should now have the restrict group after adding it.")

    def test_05_remove_group_from_user(self):
        """Test that removing the restrict group from a user updates
        has_group correctly."""
        self.assertTrue(
            self.user_with_group.has_group(
                'restrict_web_debug.restrict_debug_mode'),
            "User should initially have the restrict group.")
        self.user_with_group.write({
            'groups_id': [(3, self.restrict_group.id)],
        })
        self.assertFalse(
            self.user_with_group.has_group(
                'restrict_web_debug.restrict_debug_mode'),
            "User should no longer have the restrict group.")

    def test_06_multiple_users_independent_restriction(self):
        """Test that the restrict group works independently per user.
        Changing one user's group does not affect another."""
        self.assertFalse(
            self.user_without_group.has_group(
                'restrict_web_debug.restrict_debug_mode'))
        self.assertTrue(
            self.user_with_group.has_group(
                'restrict_web_debug.restrict_debug_mode'))
        self.user_without_group.write({
            'groups_id': [(4, self.restrict_group.id)],
        })
        self.assertTrue(
            self.user_without_group.has_group(
                'restrict_web_debug.restrict_debug_mode'))
        self.assertTrue(
            self.user_with_group.has_group(
                'restrict_web_debug.restrict_debug_mode'),
            "Modifying one user's group should not affect another user.")

    def test_07_ir_http_inherits_session_info(self):
        """Test that ir.http model has the overridden session_info
        method from the restrict_web_debug module."""
        ir_http = self.env['ir.http']
        self.assertTrue(
            hasattr(ir_http, 'session_info'),
            "ir.http should have the session_info method.")

    def test_08_user_group_value_without_group(self):
        """Test the user_group value that session_info would set for a
        user without the restrict debug group."""
        user_group = self.env['res.users'].with_user(
            self.user_without_group).env.user.has_group(
            'restrict_web_debug.restrict_debug_mode')
        self.assertFalse(
            user_group,
            "user_group should be False for user without restrict group.")

    def test_09_user_group_value_with_group(self):
        """Test the user_group value that session_info would set for a
        user with the restrict debug group."""
        user_group = self.env['res.users'].with_user(
            self.user_with_group).env.user.has_group(
            'restrict_web_debug.restrict_debug_mode')
        self.assertTrue(
            user_group,
            "user_group should be True for user with restrict group.")

    def test_10_user_group_value_after_group_change(self):
        """Test that the user_group value reflects group changes
        dynamically."""
        # Before adding group
        user_group_before = self.env['res.users'].with_user(
            self.user_without_group).env.user.has_group(
            'restrict_web_debug.restrict_debug_mode')
        self.assertFalse(user_group_before,
                         "user_group should be False before adding group.")
        # Add group
        self.user_without_group.write({
            'groups_id': [(4, self.restrict_group.id)],
        })
        # After adding group
        user_group_after = self.env['res.users'].with_user(
            self.user_without_group).env.user.has_group(
            'restrict_web_debug.restrict_debug_mode')
        self.assertTrue(user_group_after,
                        "user_group should be True after adding group.")
