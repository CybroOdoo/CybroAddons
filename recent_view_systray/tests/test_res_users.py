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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Test cases for the ResUsers model (res_users.py) in
    recent_view_systray.

    Tests the `history_limit` field added to `res.users` to control the
    maximum number of recently visited views shown in the systray.
    """

    def setUp(self):
        """Set up test environment by creating a test user."""
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Test History Limit User',
            'login': 'test_history_limit_user',
            'password': 'test_history_limit_user',
        })

    def test_history_limit_field_exists(self):
        """Test that the history_limit field exists on the res.users model."""
        self.assertIn(
            'history_limit',
            self.env['res.users']._fields,
            "The 'history_limit' field must exist on res.users."
        )

    def test_history_limit_default_value(self):
        """Test that the default value of history_limit is 15 when a
        new user is created without specifying the field."""
        self.assertEqual(
            self.test_user.history_limit, 15,
            "Default value for history_limit should be 15."
        )

    def test_history_limit_field_type_is_integer(self):
        """Test that the history_limit field is of Integer type."""
        from odoo import fields as odoo_fields
        field = self.env['res.users']._fields.get('history_limit')
        self.assertIsNotNone(field, "history_limit field must exist.")
        self.assertIsInstance(
            field, odoo_fields.Integer,
            "history_limit must be an Integer field."
        )

    def test_history_limit_can_be_set_on_creation(self):
        """Test that history_limit can be set to a custom value during
        user creation."""
        user = self.env['res.users'].create({
            'name': 'Custom Limit User',
            'login': 'custom_limit_user',
            'password': 'custom_limit_user',
            'history_limit': 20,
        })
        self.assertEqual(
            user.history_limit, 20,
            "history_limit should be 20 as set during creation."
        )

    def test_history_limit_can_be_updated(self):
        """Test that the history_limit field can be updated after user
        creation via write."""
        self.test_user.write({'history_limit': 30})
        self.assertEqual(
            self.test_user.history_limit, 30,
            "history_limit should be updated to 30 after write."
        )

    def test_history_limit_set_to_zero(self):
        """Test that history_limit can be explicitly set to 0."""
        self.test_user.write({'history_limit': 0})
        self.assertEqual(
            self.test_user.history_limit, 0,
            "history_limit should be 0 after setting it explicitly."
        )

    def test_history_limit_set_to_large_value(self):
        """Test that history_limit can store large integer values."""
        self.test_user.write({'history_limit': 1000})
        self.assertEqual(
            self.test_user.history_limit, 1000,
            "history_limit should accept and store large integer values."
        )

    def test_history_limit_field_string(self):
        """Test that the history_limit field has the correct label string."""
        field = self.env['res.users']._fields.get('history_limit')
        self.assertEqual(
            field.string, 'History Limit',
            "The string attribute of history_limit should be 'History Limit'."
        )

    def test_multiple_users_have_independent_history_limits(self):
        """Test that different users can have different independent
        history_limit values."""
        user_a = self.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a_rvs',
            'password': 'user_a_rvs',
            'history_limit': 5,
        })
        user_b = self.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b_rvs',
            'password': 'user_b_rvs',
            'history_limit': 50,
        })
        self.assertEqual(
            user_a.history_limit, 5,
            "User A's history_limit should be 5."
        )
        self.assertEqual(
            user_b.history_limit, 50,
            "User B's history_limit should be 50."
        )

    def test_admin_user_has_history_limit_field(self):
        """Test that the admin user record also exposes the history_limit
        field (inherited from res.users)."""
        admin = self.env.ref('base.user_admin')
        self.assertIn(
            'history_limit', admin._fields,
            "Admin user must also have the 'history_limit' field."
        )
