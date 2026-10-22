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
class TestResUsersPosRestrictions(TransactionCase):
    """Test suite for POS feature restriction fields on res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POS_FIELDS = [
            'pos_allow_numpad',
            'pos_allow_payments',
            'pos_allow_discount',
            'pos_allow_qty',
            'pos_allow_price_edit',
            'pos_allow_remove_order_line',
            'pos_allow_customer_selection',
            'pos_allow_plus_minus',
        ]
        cls.user_default = cls.env['res.users'].create({
            'name': 'Default Cashier User',
            'login': 'pos_default_user_test',
            'email': 'default_user@test.com',
        })
        cls.user_restricted = cls.env['res.users'].create({
            'name': 'Restricted Cashier User',
            'login': 'pos_restricted_user_test',
            'email': 'restricted_user@test.com',
            'pos_allow_numpad': False,
            'pos_allow_payments': False,
            'pos_allow_discount': False,
            'pos_allow_qty': False,
            'pos_allow_price_edit': False,
            'pos_allow_remove_order_line': False,
            'pos_allow_customer_selection': False,
            'pos_allow_plus_minus': False,
        })

    def test_default_permissions(self):
        """Verify that all POS restriction boolean fields default to True on res.users."""
        for field_name in self.POS_FIELDS:
            self.assertTrue(
                self.user_default[field_name],
                f"Field '{field_name}' should default to True on res.users."
            )

    def test_custom_permissions_creation(self):
        """Verify that POS restriction fields can be explicitly set to False on creation."""
        for field_name in self.POS_FIELDS:
            self.assertFalse(
                self.user_restricted[field_name],
                f"Field '{field_name}' should be False on user_restricted."
            )

    def test_toggle_permissions(self):
        """Verify that POS restriction fields can be updated and toggled on res.users."""
        user = self.env['res.users'].create({
            'name': 'Toggle Test User',
            'login': 'pos_toggle_user_test',
            'email': 'toggle_user@test.com',
        })

        # Initially True
        self.assertTrue(user.pos_allow_payments)
        self.assertTrue(user.pos_allow_discount)

        # Update to False
        user.write({
            'pos_allow_payments': False,
            'pos_allow_discount': False,
        })
        self.assertFalse(user.pos_allow_payments)
        self.assertFalse(user.pos_allow_discount)

        # Other fields remain True
        self.assertTrue(user.pos_allow_numpad)
        self.assertTrue(user.pos_allow_qty)

        # Toggle back to True
        user.write({'pos_allow_payments': True})
        self.assertTrue(user.pos_allow_payments)

    def test_multiple_users_independence(self):
        """Verify that restriction settings on one user do not affect another."""
        user_1 = self.env['res.users'].create({
            'name': 'User 1',
            'login': 'user_1_test_perm',
            'email': 'user1@test.com',
            'pos_allow_price_edit': False,
        })
        user_2 = self.env['res.users'].create({
            'name': 'User 2',
            'login': 'user_2_test_perm',
            'email': 'user2@test.com',
            'pos_allow_price_edit': True,
        })

        self.assertFalse(user_1.pos_allow_price_edit)
        self.assertTrue(user_2.pos_allow_price_edit)
