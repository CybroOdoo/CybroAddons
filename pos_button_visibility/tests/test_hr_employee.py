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
class TestHrEmployee(TransactionCase):
    """Test cases for button and config restriction extensions on hr.employee."""

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

        cls.button_reward = cls.env['pos.button'].search([('name', '=', 'Reward')], limit=1)
        if not cls.button_reward:
            cls.button_reward = cls.env['pos.button'].create({'name': 'Reward'})

        # POS configs
        cls.pos_config_1 = cls.env['pos.config'].create({'name': 'Branch North'})
        cls.pos_config_2 = cls.env['pos.config'].create({'name': 'Branch South'})

        # User
        cls.user_cashier = cls.env['res.users'].create({
            'name': 'Linked User Cashier',
            'login': 'linked_cashier_user',
            'email': 'linked_cashier@test.com',
        })

    def test_hr_employee_load_pos_data_fields(self):
        """Test that hr.employee _load_pos_data_fields includes pos_button_ids and pos_config_ids."""
        fields = self.env['hr.employee']._load_pos_data_fields(self.pos_config_1)
        self.assertIn(
            'pos_button_ids',
            fields,
            "hr.employee _load_pos_data_fields must include 'pos_button_ids'."
        )
        self.assertIn(
            'pos_config_ids',
            fields,
            "hr.employee _load_pos_data_fields must include 'pos_config_ids'."
        )

    def test_hr_employee_direct_restrictions(self):
        """Test direct restrictions configured on hr.employee and loaded via _load_pos_data_read."""
        employee = self.env['hr.employee'].create({
            'name': 'Direct Restricted Employee',
            'pos_config_ids': [(6, 0, [self.pos_config_1.id])],
            'pos_button_ids': [(6, 0, [self.button_price.id, self.button_refund.id])],
        })

        read_records = self.env['hr.employee']._load_pos_data_read(employee, self.pos_config_1)
        self.assertTrue(read_records)
        record = read_records[0]
        self.assertEqual(
            set(record.get('pos_button_ids', [])),
            {self.button_price.id, self.button_refund.id},
            "Direct employee button restrictions should be returned in _load_pos_data_read."
        )
        self.assertEqual(
            record.get('pos_config_ids'),
            [self.pos_config_1.id],
            "Direct employee POS config restrictions should be returned in _load_pos_data_read."
        )

    def test_hr_employee_fallback_inheritance_from_user(self):
        """Test hr.employee inheriting restrictions from linked user when employee has no direct restrictions."""
        self.user_cashier.write({
            'pos_config_ids': [(6, 0, [self.pos_config_2.id])],
            'pos_button_ids': [(6, 0, [self.button_discount.id])],
        })
        employee = self.env['hr.employee'].create({
            'name': 'Employee Inheriting From User',
            'user_id': self.user_cashier.id,
        })

        read_records = self.env['hr.employee']._load_pos_data_read(employee, self.pos_config_2)
        self.assertTrue(read_records)
        record = read_records[0]
        self.assertEqual(
            record.get('pos_button_ids'),
            [self.button_discount.id],
            "Employee without direct button restrictions should inherit them from linked user."
        )
        self.assertEqual(
            record.get('pos_config_ids'),
            [self.pos_config_2.id],
            "Employee without direct POS config restrictions should inherit them from linked user."
        )

    def test_hr_employee_override_user_restrictions(self):
        """Test that explicit employee restrictions take precedence over linked user restrictions."""
        self.user_cashier.write({
            'pos_config_ids': [(6, 0, [self.pos_config_1.id])],
            'pos_button_ids': [(6, 0, [self.button_refund.id])],
        })
        employee = self.env['hr.employee'].create({
            'name': 'Employee Overriding User',
            'user_id': self.user_cashier.id,
            'pos_config_ids': [(6, 0, [self.pos_config_2.id])],
            'pos_button_ids': [(6, 0, [self.button_reward.id])],
        })

        read_records = self.env['hr.employee']._load_pos_data_read(employee, self.pos_config_1)
        self.assertTrue(read_records)
        record = read_records[0]
        self.assertEqual(
            record.get('pos_button_ids'),
            [self.button_reward.id],
            "Explicit employee button restrictions should not be overwritten by linked user restrictions."
        )
        self.assertEqual(
            record.get('pos_config_ids'),
            [self.pos_config_2.id],
            "Explicit employee POS config restrictions should not be overwritten by linked user restrictions."
        )

    def test_hr_employee_without_restrictions_or_user(self):
        """Test employee with no user and no restrictions loaded cleanly."""
        employee = self.env['hr.employee'].create({
            'name': 'Unrestricted Employee Test',
        })
        read_records = self.env['hr.employee']._load_pos_data_read(employee, self.pos_config_1)
        self.assertTrue(read_records)
        record = read_records[0]
        self.assertFalse(
            record.get('pos_button_ids'),
            "Employee without restrictions or user should have no button restrictions."
        )
        self.assertFalse(
            record.get('pos_config_ids'),
            "Employee without restrictions or user should have no config restrictions."
        )
