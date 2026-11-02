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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test cases for res.users API key generation extension."""
import uuid
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Test cases for res.users api_key field and generate_api method."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls.env['res.users'].create({
            'name': 'API Test User 1',
            'login': 'api_test_user_1',
            'email': 'api_user1@example.com',
        })
        cls.user_2 = cls.env['res.users'].create({
            'name': 'API Test User 2',
            'login': 'api_test_user_2',
            'email': 'api_user2@example.com',
        })

    def test_01_api_key_field_initial_state(self):
        """Test that api_key is initially False and is marked as readonly."""
        self.assertFalse(self.user_1.api_key, "New user api_key should be False.")
        self.assertTrue(
            self.env['res.users']._fields['api_key'].readonly,
            "api_key field must be readonly."
        )

    def test_02_generate_api_new_user(self):
        """Test generate_api generates a valid UUID and sets it on the user."""
        key = self.user_1.generate_api(self.user_1.login)

        self.assertTrue(key, "generate_api should return an API key.")
        # Verify valid UUID format
        parsed_uuid = uuid.UUID(key)
        self.assertEqual(str(parsed_uuid), key, "Returned key must be a valid UUID string.")
        self.assertEqual(
            self.user_1.api_key,
            key,
            "User's api_key field must match the returned key."
        )

    def test_03_generate_api_idempotent_existing_key(self):
        """Test generate_api returns existing key without regenerating."""
        initial_key = self.user_1.generate_api(self.user_1.login)
        self.assertTrue(initial_key)

        # Call generate_api second time
        second_key = self.user_1.generate_api(self.user_1.login)
        self.assertEqual(
            initial_key,
            second_key,
            "Subsequent generate_api call must return the exact same API key."
        )
        self.assertEqual(self.user_1.api_key, initial_key)

    def test_04_generate_api_multiple_users_unique(self):
        """Test that generate_api generates unique keys for different users."""
        key_1 = self.user_1.generate_api(self.user_1.login)
        key_2 = self.user_2.generate_api(self.user_2.login)

        self.assertTrue(key_1)
        self.assertTrue(key_2)
        self.assertNotEqual(
            key_1,
            key_2,
            "Different users must have distinct API keys."
        )

    def test_05_generate_api_nonexistent_user(self):
        """Test generate_api with a non-existent login returns False without error."""
        result = self.env['res.users'].generate_api('non_existent_login_xyz_999')
        self.assertFalse(
            result,
            "generate_api should return False when no matching user is found."
        )

    def test_06_generate_api_restricted_user_environment(self):
        """Test generate_api succeeds even when called in a restricted user's environment."""
        # Use user_1's environment to generate key for user_2
        user_2_env = self.env['res.users'].with_user(self.user_1)
        key = user_2_env.generate_api(self.user_2.login)

        self.assertTrue(key, "generate_api should succeed via sudo() search.")
        self.assertEqual(self.user_2.api_key, key)
