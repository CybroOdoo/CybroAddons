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

"""Test cases for hr.employee.public model in pos_discount_manager."""
from unittest.mock import patch

from odoo import models
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestHrEmployeePublic(TransactionCase):
    """Test cases for hr.employee.public discount limit features."""

    def setUp(self):
        """Set up test data for hr.employee.public tests."""
        super().setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Public Employee Cashier',
            'limited_discount': 7.5,
        })
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Config Public',
        })

    def test_load_pos_data_fields(self):
        """Test _load_pos_data_fields appends limited_discount on hr.employee.public."""
        with patch.object(models.Model, '_load_pos_data_fields', create=True, return_value=['name']):
            fields = self.env['hr.employee.public']._load_pos_data_fields(self.pos_config.id)
            self.assertIsInstance(fields, list, "_load_pos_data_fields should return a list.")
            self.assertIn(
                'limited_discount', fields,
                "'limited_discount' field should be loaded in pos data for hr.employee.public."
            )
            self.assertIn('name', fields, "Base fields from super should be preserved.")

    def test_load_pos_data_fields_without_config(self):
        """Test _load_pos_data_fields works when config_id is False."""
        with patch.object(models.Model, '_load_pos_data_fields', create=True, return_value=['id']):
            fields = self.env['hr.employee.public']._load_pos_data_fields(False)
            self.assertIsInstance(fields, list, "_load_pos_data_fields should return a list.")
            self.assertIn('limited_discount', fields)

    def test_hr_employee_public_discount_sync(self):
        """Test if public employee model syncs limited discount field properly."""
        self.env.flush_all()
        public_employee = self.env['hr.employee.public'].search([
            ('id', '=', self.employee.id)
        ])
        if not public_employee:
            public_employee = self.env['hr.employee.public'].search([
                ('employee_id', '=', self.employee.id)
            ])

        if public_employee:
            self.assertEqual(
                public_employee.limited_discount, 7.5,
                "Public employee related discount limit is incorrect."
            )
            # Test update synchronization
            self.employee.write({'limited_discount': 12.0})
            self.env.flush_all()
            self.assertEqual(
                public_employee.limited_discount, 12.0,
                "Public employee related discount limit did not update."
            )

    def test_hr_employee_public_default_discount(self):
        """Test default discount limit on public employee when created with 0.0."""
        emp_default = self.env['hr.employee'].create({
            'name': 'Default Public Cashier',
        })
        self.env.flush_all()
        public_emp = self.env['hr.employee.public'].search([
            ('id', '=', emp_default.id)
        ])
        if not public_emp:
            public_emp = self.env['hr.employee.public'].search([
                ('employee_id', '=', emp_default.id)
            ])
        if public_emp:
            self.assertEqual(
                public_emp.limited_discount, 0.0,
                "Public employee default discount should be 0.0."
            )
