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
class TestResUsers(TransactionCase):
    """Test cases for button and config restriction extensions on res.users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Buttons
        cls.button_refund = cls.env['pos.button'].search([('name', '=', 'Refund')], limit=1)
        if not cls.button_refund:
            cls.button_refund = cls.env['pos.button'].create({'name': 'Refund'})

        cls.button_price = cls.env['pos.button'].search([('name', '=', 'Price')], limit=1)
        if not cls.button_price:
            cls.button_price = cls.env['pos.button'].create({'name': 'Price'})

        cls.button_discount = cls.env['pos.button'].search([('name', '=', 'Discount')], limit=1)
        if not cls.button_discount:
            cls.button_discount = cls.env['pos.button'].create({'name': 'Discount'})

        # POS configs
        cls.pos_config_1 = cls.env['pos.config'].create({'name': 'Store Alpha'})
        cls.pos_config_2 = cls.env['pos.config'].create({'name': 'Store Beta'})

        # Test users
        cls.user_cashier = cls.env['res.users'].create({
            'name': 'POS Cashier User',
            'login': 'pos_cashier_user_test',
            'email': 'cashier_user@test.com',
        })
        cls.user_secondary = cls.env['res.users'].create({
            'name': 'POS Secondary User',
            'login': 'pos_secondary_user_test',
            'email': 'secondary_user@test.com',
        })

    def test_res_users_load_pos_data_fields(self):
        """Test that res.users _load_pos_data_fields includes pos_button_ids and pos_config_ids."""
        fields = self.env['res.users']._load_pos_data_fields(self.pos_config_1)
        self.assertIn(
            'pos_button_ids',
            fields,
            "res.users _load_pos_data_fields must include 'pos_button_ids'."
        )
        self.assertIn(
            'pos_config_ids',
            fields,
            "res.users _load_pos_data_fields must include 'pos_config_ids'."
        )

    def test_pos_button_visibility(self):
        """Test pos_button_visibility returns list of restricted button names."""
        button_ids = [self.button_refund.id, self.button_price.id]
        names = self.user_cashier.pos_button_visibility(button_ids)
        self.assertEqual(
            set(names),
            {'Refund', 'Price'},
            "pos_button_visibility should return the names of the given button IDs."
        )

        empty_names = self.user_cashier.pos_button_visibility([])
        self.assertEqual(
            empty_names,
            [],
            "pos_button_visibility should return an empty list when given empty IDs."
        )

    def test_res_users_restriction_configuration(self):
        """Test configuring, updating, and clearing restrictions on res.users."""
        self.user_cashier.write({
            'pos_config_ids': [(6, 0, [self.pos_config_1.id])],
            'pos_button_ids': [(6, 0, [self.button_refund.id, self.button_discount.id])],
        })

        self.assertIn(self.pos_config_1, self.user_cashier.pos_config_ids)
        self.assertNotIn(self.pos_config_2, self.user_cashier.pos_config_ids)
        self.assertEqual(
            set(self.user_cashier.pos_button_ids.ids),
            {self.button_refund.id, self.button_discount.id}
        )

        # Update restriction
        self.user_cashier.write({
            'pos_button_ids': [(6, 0, [self.button_price.id])],
        })
        self.assertEqual(self.user_cashier.pos_button_ids.ids, [self.button_price.id])

        # Clear restrictions
        self.user_cashier.write({
            'pos_config_ids': [(5, 0, 0)],
            'pos_button_ids': [(5, 0, 0)],
        })
        self.assertFalse(self.user_cashier.pos_config_ids)
        self.assertFalse(self.user_cashier.pos_button_ids)

    def test_res_users_isolation(self):
        """Test that button restrictions on one user do not affect another user."""
        self.user_cashier.write({
            'pos_config_ids': [(6, 0, [self.pos_config_1.id])],
            'pos_button_ids': [(6, 0, [self.button_refund.id])],
        })
        self.user_secondary.write({
            'pos_config_ids': [(6, 0, [self.pos_config_2.id])],
            'pos_button_ids': [(6, 0, [self.button_price.id])],
        })

        self.assertEqual(self.user_cashier.pos_button_ids.ids, [self.button_refund.id])
        self.assertEqual(self.user_cashier.pos_config_ids.ids, [self.pos_config_1.id])

        self.assertEqual(self.user_secondary.pos_button_ids.ids, [self.button_price.id])
        self.assertEqual(self.user_secondary.pos_config_ids.ids, [self.pos_config_2.id])
