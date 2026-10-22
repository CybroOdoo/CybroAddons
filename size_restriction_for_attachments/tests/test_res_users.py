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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResUsersRestriction(TransactionCase):
    """Test cases for size restriction fields added to res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Attachment User',
            'login': 'test_attachment_user',
            'email': 'test_attachment_user@example.com',
        })

    def test_default_restriction_settings(self):
        """Test default values of set_restriction and max_size."""
        user = self.env['res.users'].create({
            'name': 'Default Settings User',
            'login': 'default_settings_user',
            'email': 'default_settings@example.com',
        })
        self.assertFalse(
            user.set_restriction,
            "set_restriction should default to False."
        )
        self.assertEqual(
            user.max_size,
            0.0,
            "max_size should default to 0.0."
        )

    def test_enable_restriction(self):
        """Test enabling size restriction and setting maximum size limit."""
        self.test_user.write({
            'set_restriction': True,
            'max_size': 5.0,
        })
        self.assertTrue(
            self.test_user.set_restriction,
            "set_restriction should be True after enabling."
        )
        self.assertEqual(
            self.test_user.max_size,
            5.0,
            "max_size should be set to 5.0 MB."
        )

    def test_update_restriction_size(self):
        """Test updating maximum size limit."""
        self.test_user.write({
            'set_restriction': True,
            'max_size': 2.5,
        })
        self.assertEqual(self.test_user.max_size, 2.5)

        self.test_user.write({
            'max_size': 10.0,
        })
        self.assertEqual(self.test_user.max_size, 10.0)

    def test_disable_restriction(self):
        """Test disabling restriction while keeping max_size value intact."""
        self.test_user.write({
            'set_restriction': True,
            'max_size': 4.0,
        })
        self.assertTrue(self.test_user.set_restriction)

        self.test_user.write({
            'set_restriction': False,
        })
        self.assertFalse(self.test_user.set_restriction)
        self.assertEqual(self.test_user.max_size, 4.0)

    def test_multiple_users_isolation(self):
        """Test that size restrictions on one user do not affect others."""
        user_a = self.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a',
            'email': 'user_a@example.com',
            'set_restriction': True,
            'max_size': 2.0,
        })
        user_b = self.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b',
            'email': 'user_b@example.com',
            'set_restriction': False,
            'max_size': 0.0,
        })
        user_c = self.env['res.users'].create({
            'name': 'User C',
            'login': 'user_c',
            'email': 'user_c@example.com',
            'set_restriction': True,
            'max_size': 15.0,
        })

        self.assertTrue(user_a.set_restriction)
        self.assertEqual(user_a.max_size, 2.0)

        self.assertFalse(user_b.set_restriction)
        self.assertEqual(user_b.max_size, 0.0)

        self.assertTrue(user_c.set_restriction)
        self.assertEqual(user_c.max_size, 15.0)
