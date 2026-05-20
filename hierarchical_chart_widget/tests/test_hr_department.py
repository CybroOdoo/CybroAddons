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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestHrDepartment(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.parent_department = cls.env['hr.department'].create({
            'name': 'Management',
        })
        cls.child_department = cls.env['hr.department'].create({
            'name': 'Sales',
            'parent_id': cls.parent_department.id,
        })

    def test_department_hierarchy(self):
        """Test parent-child department relation."""
        self.assertEqual(
            self.child_department.parent_id,
            self.parent_department
        )
        self.assertIn(
            self.child_department,
            self.parent_department.child_ids
        )

    def test_get_child_dept(self):
        """Test get_child_dept method."""
        result = self.env['hr.department'].get_child_dept(
            self.parent_department.id
        )
        self.assertEqual(
            result['self'],
            'Management'
        )
        self.assertEqual(
            result['child'][0]['name'],
            'Sales'
        )

    def test_create_department(self):
        """Test overridden create method."""
        department = self.env['hr.department'].create({
            'name': 'Accounts',
            'parent_id': self.parent_department.id,
        })
        self.assertTrue(
            department.is_parent_child
        )

    def test_write_department(self):
        """Test overridden write method."""
        department = self.env['hr.department'].create({
            'name': 'HR',
        })
        department.write({
            'parent_id': self.parent_department.id
        })
        self.assertTrue(
            department.is_parent_child
        )
