# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from odoo.tests.common import TransactionCase

class TestImportAttendance(TransactionCase):

    def setUp(self):
        super(TestImportAttendance, self).setUp()
        self.Wizard = self.env['import.attendance']
        self.Employee = self.env['hr.employee'].create({'name': 'John Doe'})

    def test_action_import_attendance_csv(self):
        """Test importing attendance from CSV"""
        csv_content = "Employee,Check In,Check Out\nJohn Doe,2026-06-01 08:00:00,2026-06-01 17:00:00"
        wizard = self.Wizard.create({
            'file_type': 'csv',
            'file_upload': base64.b64encode(csv_content.encode('utf-8'))
        })
        
        wizard.action_import_attendance()
        
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.Employee.id)])
        self.assertEqual(len(attendance), 1)
        self.assertEqual(str(attendance.check_in), '2026-06-01 08:00:00')
