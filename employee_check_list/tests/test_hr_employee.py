# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Abhijith CK(odoo@cybrosys.com)
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
#############################################################################
from odoo.tests.common import TransactionCase

class TestEmployeeChecklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestEmployeeChecklist, cls).setUpClass()
        
        # Create Checklists
        cls.entry_checklist = cls.env['employee.checklist'].create({
            'name': 'Entry Checklist 1',
            'document_type': 'entry',
        })
        cls.exit_checklist = cls.env['employee.checklist'].create({
            'name': 'Exit Checklist 1',
            'document_type': 'exit',
        })
        
        # Create Employee
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
        })

    def test_entry_exit_progress(self):
        # Initial progress should be 0
        self.assertEqual(self.employee.entry_progress, 0.0)
        self.assertEqual(self.employee.exit_progress, 0.0)

        # Create entry document
        entry_document = self.env['hr.employee.document'].create({
            'name': 'Entry Doc',
            'document_id': self.entry_checklist.id,
            'employee_id': self.employee.id,
        })
        
        # Entry checklist should be added to employee and progress updated
        self.assertIn(self.entry_checklist, self.employee.entry_checklist_ids)
        self.assertTrue(self.employee.entry_progress > 0.0)

        # Create exit document
        exit_document = self.env['hr.employee.document'].create({
            'name': 'Exit Doc',
            'document_id': self.exit_checklist.id,
            'employee_id': self.employee.id,
        })
        
        # Exit checklist should be added to employee and progress updated
        self.assertIn(self.exit_checklist, self.employee.exit_checklist_ids)
        self.assertTrue(self.employee.exit_progress > 0.0)
        
        # Delete entry document
        entry_document.unlink()
        self.assertNotIn(self.entry_checklist, self.employee.entry_checklist_ids)
        self.assertEqual(self.employee.entry_progress, 0.0)

        # Delete exit document
        exit_document.unlink()
        self.assertNotIn(self.exit_checklist, self.employee.exit_checklist_ids)
        self.assertEqual(self.employee.exit_progress, 0.0)

