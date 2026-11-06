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
from odoo.tests import TransactionCase, tagged

POS_FLAGS = [
    'disable_payment',
    'disable_customer',
    'disable_plus_minus',
    'disable_numpad',
    'disable_qty',
    'disable_discount',
    'disable_price',
    'disable_remove_button',
]


@tagged('post_install', '-at_install')
class TestHrEmployeePosFlags(TransactionCase):
    """Tests for the POS UI control flags added to hr.employee."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['hr.employee'].create({'name': 'POS Test Employee'})
        cls.pos_config = (
            cls.env['pos.config'].search([], limit=1)
            or cls.env['pos.config'].create({'name': 'Test POS Config'})
        )

    def test_01_flags_exist_and_are_boolean(self):
        """Every flag is defined on hr.employee as a Boolean field."""
        fields_get = self.env['hr.employee'].fields_get(POS_FLAGS)
        for flag in POS_FLAGS:
            with self.subTest(flag=flag):
                self.assertIn(flag, fields_get)
                self.assertEqual(fields_get[flag]['type'], 'boolean')

    def test_02_flags_default_to_false(self):
        """A new employee has no restriction by default."""
        for flag in POS_FLAGS:
            with self.subTest(flag=flag):
                self.assertFalse(self.employee[flag])

    def test_03_flags_can_be_set_individually(self):
        """Setting one flag leaves all the others untouched."""
        for flag in POS_FLAGS:
            with self.subTest(flag=flag):
                employee = self.env['hr.employee'].create({
                    'name': f'Employee {flag}',
                    flag: True,
                })
                self.assertTrue(employee[flag])
                for other in POS_FLAGS:
                    if other != flag:
                        self.assertFalse(employee[other])

    def test_04_flags_can_be_toggled_with_write(self):
        """Flags can be turned on and off again."""
        self.employee.write({flag: True for flag in POS_FLAGS})
        for flag in POS_FLAGS:
            self.assertTrue(self.employee[flag])
        self.employee.write({flag: False for flag in POS_FLAGS})
        for flag in POS_FLAGS:
            self.assertFalse(self.employee[flag])

    def test_05_load_pos_data_fields_includes_flags(self):
        """The POS loader exposes all the custom flags."""
        result = self.env['hr.employee']._load_pos_data_fields(self.pos_config)
        for flag in POS_FLAGS:
            with self.subTest(flag=flag):
                self.assertIn(flag, result)

    def test_06_load_pos_data_fields_keeps_base_fields(self):
        """The override adds to the standard fields instead of replacing them."""
        result = self.env['hr.employee']._load_pos_data_fields(self.pos_config)
        self.assertIn('name', result)
        self.assertGreater(len(result), len(POS_FLAGS))

    def test_07_load_pos_data_fields_has_no_duplicates(self):
        """Each field appears once in the loader result."""
        result = self.env['hr.employee']._load_pos_data_fields(self.pos_config)
        self.assertEqual(len(result), len(set(result)))

    def test_08_load_pos_data_values(self):
        """Verify that _load_pos_data_read returns the actual flag values for POS session."""
        self.employee.write({
            'disable_payment': True,
            'disable_customer': True,
            'disable_qty': False,
        })
        records = self.env['hr.employee']._load_pos_data_read(self.employee, self.pos_config)
        self.assertTrue(records)
        emp_data = records[0]
        self.assertTrue(emp_data.get('disable_payment'))
        self.assertTrue(emp_data.get('disable_customer'))
        self.assertFalse(emp_data.get('disable_qty'))

    def test_09_employee_permission_matrix(self):
        """Test multiple employees having distinct permission configurations."""
        emp_restricted = self.env['hr.employee'].create({
            'name': 'Restricted Cashier',
            'disable_payment': True,
            'disable_customer': True,
            'disable_numpad': True,
        })
        emp_unrestricted = self.env['hr.employee'].create({
            'name': 'Unrestricted Cashier',
        })
        self.assertTrue(emp_restricted.disable_payment)
        self.assertTrue(emp_restricted.disable_customer)
        self.assertTrue(emp_restricted.disable_numpad)
        self.assertFalse(emp_unrestricted.disable_payment)
        self.assertFalse(emp_unrestricted.disable_customer)
        self.assertFalse(emp_unrestricted.disable_numpad)
