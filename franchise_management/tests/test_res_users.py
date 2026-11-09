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
#############################################################################
"""Test cases for Res Users inherited model."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """Test suite for res.users extension."""

    def test_is_dealer_user_field(self):
        """Test is_dealer_user boolean field default and modification."""
        user = self.env['res.users'].create({
            'name': 'Test Dealer User',
            'login': 'dealer_user_test@example.com',
            'email': 'dealer_user_test@example.com',
        })
        self.assertFalse(user.is_dealer_user)
        user.is_dealer_user = True
        self.assertTrue(user.is_dealer_user)

        dealer_users = self.env['res.users'].search([('is_dealer_user', '=', True)])
        self.assertIn(user, dealer_users)

