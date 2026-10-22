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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDepartment(TransactionCase):
    """Test suite for department model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Department = cls.env['queue.department']

    def test_department_creation(self):
        """Test creating a department record with valid values."""
        dept = self.Department.create({
            'name': 'Customer Support',
            'code': 'CS'
        })
        self.assertEqual(dept.name, 'Customer Support')
        self.assertEqual(dept.code, 'CS')

    def test_department_required_name(self):
        """Test that department creation without a name raises an exception."""
        with self.assertRaises(Exception):
            self.Department.create({
                'code': 'CS'
            })

    def test_department_required_code(self):
        """Test that department creation without a code raises an exception."""
        with self.assertRaises(Exception):
            self.Department.create({
                'name': 'Customer Support'
            })
