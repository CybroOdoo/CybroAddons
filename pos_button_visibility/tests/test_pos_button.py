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
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosButton(TransactionCase):
    """Test cases for the pos.button model and access rights."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Default buttons
        cls.button_refund = cls.env['pos.button'].search([('name', '=', 'Refund')], limit=1)
        if not cls.button_refund:
            cls.button_refund = cls.env['pos.button'].create({'name': 'Refund'})

        cls.button_price = cls.env['pos.button'].search([('name', '=', 'Price')], limit=1)
        if not cls.button_price:
            cls.button_price = cls.env['pos.button'].create({'name': 'Price'})

        cls.button_discount = cls.env['pos.button'].search([('name', '=', 'Discount')], limit=1)
        if not cls.button_discount:
            cls.button_discount = cls.env['pos.button'].create({'name': 'Discount'})

        cls.button_reward = cls.env['pos.button'].search([('name', '=', 'Reward')], limit=1)
        if not cls.button_reward:
            cls.button_reward = cls.env['pos.button'].create({'name': 'Reward'})

        cls.pos_config = cls.env['pos.config'].create({'name': 'Test POS Store'})

        # Groups
        cls.group_pos_manager = cls.env.ref('point_of_sale.group_pos_manager')
        cls.group_internal = cls.env.ref('base.group_user')

        # Test users
        cls.user_manager = cls.env['res.users'].create({
            'name': 'POS Test Manager',
            'login': 'pos_test_manager_button',
            'email': 'pos_manager_button@test.com',
            'group_ids': [(6, 0, [cls.group_pos_manager.id, cls.group_internal.id])],
        })
        cls.user_internal = cls.env['res.users'].create({
            'name': 'Standard Internal User',
            'login': 'standard_internal_user_button',
            'email': 'internal_button@test.com',
            'group_ids': [(6, 0, [cls.group_internal.id])],
        })

    def test_default_buttons_exist(self):
        """Test that default POS buttons exist in pos.button model."""
        button_names = self.env['pos.button'].search([]).mapped('name')
        for expected_name in ['Refund', 'Price', 'Discount', 'Reward']:
            self.assertIn(
                expected_name,
                button_names,
                f"Default button '{expected_name}' should exist in pos.button."
            )

    def test_pos_button_load_fields(self):
        """Test that pos.button _load_pos_data_fields returns ['name']."""
        fields = self.env['pos.button']._load_pos_data_fields(self.pos_config)
        self.assertIn(
            'name',
            fields,
            "pos.button _load_pos_data_fields must return 'name'."
        )

    def test_create_custom_pos_button(self):
        """Test creating and reading a custom POS button."""
        custom_btn = self.env['pos.button'].create({'name': 'Custom Button Action'})
        self.assertTrue(custom_btn.id)
        self.assertEqual(custom_btn.name, 'Custom Button Action')

    def test_pos_button_security_manager_crud(self):
        """Test POS Manager has full CRUD access on pos.button model."""
        manager_env = self.env['pos.button'].with_user(self.user_manager)

        # Create
        btn = manager_env.create({'name': 'Manager Button'})
        self.assertTrue(btn.id)

        # Read
        btn_read = manager_env.browse(btn.id)
        self.assertEqual(btn_read.name, 'Manager Button')

        # Write
        btn.write({'name': 'Manager Button Updated'})
        self.assertEqual(btn.name, 'Manager Button Updated')

        # Unlink
        btn.unlink()
        self.assertFalse(manager_env.search([('name', '=', 'Manager Button Updated')]))

    def test_pos_button_security_internal_user_readonly(self):
        """Test regular internal user has read-only access on pos.button."""
        user_env = self.env['pos.button'].with_user(self.user_internal)

        # Read should succeed
        buttons = user_env.search([])
        self.assertTrue(buttons, "Internal user should be able to read pos.button records.")

        # Create should raise AccessError
        with self.assertRaises(AccessError):
            user_env.create({'name': 'Unauthorized Button'})

        # Write should raise AccessError
        with self.assertRaises(AccessError):
            self.button_refund.with_user(self.user_internal).write({'name': 'Modified Refund'})

        # Unlink should raise AccessError
        with self.assertRaises(AccessError):
            self.button_refund.with_user(self.user_internal).unlink()
