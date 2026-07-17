# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests.common import TransactionCase

class TestFoVisit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestFoVisit, cls).setUpClass()
        cls.visitor = cls.env['fo.visitor'].create({
            'name': 'Test Visitor',
            'phone': '1234567890',
            'email': 'visitor@test.com',
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        cls.purpose = cls.env['fo.purpose'].create({
            'name': 'Meeting',
        })
        cls.visit = cls.env['fo.visit'].create({
            'visitor_id': cls.visitor.id,
            'phone': '1234567890',
            'email': 'visitor@test.com',
            'reason_ids': [(6, 0, [cls.purpose.id])],
            'employee_id': cls.employee.id,
        })

    def test_create_sequence(self):
        """Test if the sequence is created"""
        self.assertNotEqual(self.visit.name, 'New', "Sequence should be generated")

    def test_action_cancel(self):
        """Test action cancel"""
        self.visit.action_cancel()
        self.assertEqual(self.visit.state, 'cancel', "State should be 'cancel'")

    def test_action_check_in_out(self):
        """Test action check in and check out"""
        self.visit.action_check_in()
        self.assertEqual(self.visit.state, 'check_in', "State should be 'check_in'")
        self.assertTrue(self.visit.check_in_date, "Check-in date should be set")

        self.visit.action_check_out()
        self.assertEqual(self.visit.state, 'check_out', "State should be 'check_out'")
        self.assertTrue(self.visit.check_out_date, "Check-out date should be set")

    def test_onchange_visitor_id(self):
        """Test onchange visitor id"""
        visit_form = self.env['fo.visit'].new({
            'visitor_id': self.visitor.id,
        })
        visit_form._onchange_visitor_id()
        self.assertEqual(visit_form.phone, '1234567890', "Phone should autofill")
        self.assertEqual(visit_form.email, 'visitor@test.com', "Email should autofill")

    def test_onchange_employee_id(self):
        """Test onchange employee id"""
        department = self.env['hr.department'].create({'name': 'IT'})
        employee = self.env['hr.employee'].create({
            'name': 'Emp with Dept',
            'department_id': department.id,
        })
        visit_form = self.env['fo.visit'].new({
            'employee_id': employee.id,
        })
        visit_form._onchange_employee_id()
        self.assertEqual(visit_form.department_id.id, department.id, "Department should autofill")
