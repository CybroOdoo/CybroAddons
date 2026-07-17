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
from odoo.exceptions import UserError

class TestFoPropertyCounter(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestFoPropertyCounter, cls).setUpClass()
        cls.employee = cls.env['hr.employee'].create({'name': 'Test Employee'})
        cls.property_counter = cls.env['fo.property.counter'].create({
            'employee_id': cls.employee.id,
            'date': '2026-04-30',
        })

    def test_action_cancel(self):
        """Test action cancel"""
        self.property_counter.action_cancel()
        self.assertEqual(self.property_counter.state, 'cancel', "State should be 'cancel'")

    def test_action_taken_in_out(self):
        """Test the action taken in and out"""
        belonging1 = self.env['fo.belongings'].create({
            'property_counter_id': self.property_counter.id,
            'property_name': 'Laptop',
            'property_count': '1',
            'permission': '0', # Allowed
        })
        belonging2 = self.env['fo.belongings'].create({
            'property_counter_id': self.property_counter.id,
            'property_name': 'Camera',
            'property_count': '1',
            'permission': '1', # Not Allowed
        })
        
        # Test numbering computation
        self.property_counter.belonging_ids = [(6, 0, [belonging1.id, belonging2.id])]
        self.assertEqual(belonging1.number, 1, "First belonging should have number 1")
        self.assertEqual(belonging2.number, 2, "Second belonging should have number 2")
        
        self.property_counter.action_taken_in()
        self.assertEqual(self.property_counter.state, 'taken_in', "State should be 'taken_in'")

        self.property_counter.action_taken_out()
        self.assertEqual(self.property_counter.state, 'taken_out', "State should be 'taken_out'")

    def test_action_taken_in_exception_no_count(self):
        """Test action taken in with missing count exception"""
        self.env['fo.belongings'].create({
            'property_counter_id': self.property_counter.id,
            'property_name': 'Bag',
            # property_count is missing
            'permission': '0',
        })
        with self.assertRaises(UserError):
            self.property_counter.action_taken_in()

    def test_action_taken_in_exception_no_property(self):
        """Test action taken in with no allowed properties exception"""
        belonging = self.env['fo.belongings'].create({
            'property_counter_id': self.property_counter.id,
            'property_name': 'Bag',
            'property_count': '1',
            'permission': '1', # Not allowed
        })
        self.property_counter.belonging_ids = [(6, 0, [belonging.id])]
        with self.assertRaises(UserError):
            self.property_counter.action_taken_in()
