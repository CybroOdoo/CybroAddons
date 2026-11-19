# -*- coding: utf-8 -*-
#################################################################################
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
################################################################################

"""Test cases for hr.employee model in pos_discount_manager."""
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrEmployee(TransactionCase):
    """Test cases for hr.employee discount limit features."""

    def setUp(self):
        """Set up test data for hr.employee tests."""
        super().setUp()
        self.manager = self.env['hr.employee'].create({
            'name': 'Test Manager',
            'pin': '1234',
        })
        self.cashier = self.env['hr.employee'].create({
            'name': 'Test Cashier',
            'parent_id': self.manager.id,
            'limited_discount': 5.0,
        })
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Config',
        })

    def test_limited_discount_default(self):
        """Test default value of limited_discount on hr.employee."""
        employee = self.env['hr.employee'].create({
            'name': 'Default Discount Employee',
        })
        self.assertEqual(
            employee.limited_discount, 0.0,
            "Default limited_discount should be 0.0"
        )

    def test_limited_discount_assignment(self):
        """Test custom value assignment and reading of limited_discount."""
        self.assertEqual(
            self.cashier.limited_discount, 5.0,
            "Discount limit not set correctly on cashier."
        )

    def test_limited_discount_write(self):
        """Test updating limited_discount on hr.employee."""
        self.cashier.write({'limited_discount': 10.0})
        self.assertEqual(
            self.cashier.limited_discount, 10.0,
            "Discount limit was not updated correctly."
        )

    def test_employee_manager_and_pin(self):
        """Test manager assignment and PIN setup for discount approval."""
        self.assertEqual(
            self.cashier.parent_id, self.manager,
            "Manager not set correctly on employee."
        )
        self.assertEqual(
            self.manager.pin, '1234',
            "PIN not set correctly on manager."
        )

    def test_load_pos_data_fields(self):
        """Test _load_pos_data_fields appends required fields on hr.employee."""
        fields = self.env['hr.employee']._load_pos_data_fields(self.pos_config.id)
        self.assertIsInstance(fields, list, "_load_pos_data_fields should return a list.")
        self.assertIn(
            'limited_discount', fields,
            "'limited_discount' field should be loaded in pos data."
        )
        self.assertIn(
            'parent_id', fields,
            "'parent_id' field should be loaded in pos data."
        )
        self.assertIn(
            'pin', fields,
            "'pin' field should be loaded in pos data."
        )

    def test_load_pos_data_fields_without_config(self):
        """Test _load_pos_data_fields works when config_id is False."""
        fields = self.env['hr.employee']._load_pos_data_fields(False)
        self.assertIsInstance(fields, list, "_load_pos_data_fields should return a list.")
        self.assertIn('limited_discount', fields)
        self.assertIn('parent_id', fields)
        self.assertIn('pin', fields)
