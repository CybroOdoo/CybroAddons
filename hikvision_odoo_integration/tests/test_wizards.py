# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from datetime import date
from unittest.mock import patch
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestWizards(TransactionCase):
    """Test suite for Hikvision integration wizard models."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_manager_user = cls.env['res.users'].create({
            'name': 'HR Admin Manager',
            'login': 'hradmin@example.com',
            'email': 'hradmin@example.com',
            'groups_id': [(6, 0, [cls.env.ref('hr.group_hr_manager').id, cls.env.ref('base.group_user').id])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Wizard Employee',
            'work_email': 'wizardemp@example.com',
        })
        cls.approval = cls.env['attendance.approval'].create({
            'employee_id': cls.employee.id,
            'date': date.today(),
            'reason': 'Late Arrival',
            'state': 'submitted',
        })
        cls.device = cls.env['hikvision.device'].create({
            'name': 'Entrance Gate',
            'ip_address': '192.168.1.150',
            'username': 'admin',
            'password': 'pass',
        })
        cls.leave_type = cls.env['hr.leave.type'].create({
            'name': 'Casual Leave',
            'requires_allocation': 'no',
        })

    def test_rejection_wizard_no_leave(self):
        """Test rejection without leave creation."""
        wizard = self.env['attendance.rejection.wizard'].with_user(self.hr_manager_user).create({
            'approval_id': self.approval.id,
            'rejected_reason': 'Reason invalid',
            'leave_type': 'no_leave',
        })
        res = wizard.action_confirm_rejection()
        self.assertEqual(self.approval.state, 'rejected')
        self.assertEqual(self.approval.rejected_reason, 'Reason invalid')
        self.assertEqual(res['type'], 'ir.actions.act_window_close')

    def test_rejection_wizard_with_leave(self):
        """Test rejection with automatic full day leave creation."""
        wizard = self.env['attendance.rejection.wizard'].with_user(self.hr_manager_user).create({
            'approval_id': self.approval.id,
            'rejected_reason': 'Unexcused shortfall',
            'leave_type': 'full_day',
            'time_off_type_id': self.leave_type.id,
        })
        wizard.action_confirm_rejection()
        self.assertEqual(self.approval.state, 'rejected')

        leave = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee.id),
            ('holiday_status_id', '=', self.leave_type.id)
        ], limit=1)
        self.assertTrue(leave.exists())
        self.assertEqual(leave.state, 'validate')

    def test_rejection_wizard_missing_time_off_type(self):
        """Test error when confirming leave rejection without selecting leave type."""
        wizard = self.env['attendance.rejection.wizard'].with_user(self.hr_manager_user).create({
            'approval_id': self.approval.id,
            'rejected_reason': 'Shortfall',
            'leave_type': 'full_day',
            'time_off_type_id': False,
            'auto_select_leave': False,
        })
        with self.assertRaises(UserError):
            wizard.action_confirm_rejection()

    def test_hikvision_management_employee_computation(self):
        """Test filtering employees in management wizard based on action."""
        emp_with_hik = self.env['hr.employee'].create({
            'name': 'Employee With Device ID',
            'hikvision_number': '7001',
        })
        emp_without_hik = self.env['hr.employee'].create({
            'name': 'Employee Without Device ID',
        })

        wizard_create = self.env['hikvision.management'].create({
            'manage_users': 'create_user',
            'device_id': self.device.id,
        })
        wizard_create._compute_employee_ids()
        self.assertIn(emp_without_hik.id, wizard_create.employee_ids.ids)
        self.assertNotIn(emp_with_hik.id, wizard_create.employee_ids.ids)

        wizard_update = self.env['hikvision.management'].create({
            'manage_users': 'update_user',
            'device_id': self.device.id,
        })
        wizard_update._compute_employee_ids()
        self.assertIn(emp_with_hik.id, wizard_update.employee_ids.ids)
        self.assertNotIn(emp_without_hik.id, wizard_update.employee_ids.ids)

    @patch('hikvision.device.HikvisionDevice.create_hikvision_user')
    def test_hikvision_management_action_confirm_create(self, mock_create):
        """Test confirming user creation via management wizard."""
        emp = self.env['hr.employee'].create({'name': 'New Device Emp'})
        wizard = self.env['hikvision.management'].create({
            'manage_users': 'create_user',
            'device_id': self.device.id,
            'employee_id': emp.id,
        })
        res = wizard.action_confirm_user_management()
        mock_create.assert_called_once_with(emp)
        self.assertEqual(res['type'], 'ir.actions.client')

    @patch('hikvision.device.HikvisionDevice.delete_hikvision_user')
    def test_hikvision_management_action_confirm_delete(self, mock_delete):
        """Test confirming user deletion via management wizard."""
        emp = self.env['hr.employee'].create({'name': 'Delete Emp', 'hikvision_number': '999'})
        wizard = self.env['hikvision.management'].create({
            'manage_users': 'delete_user',
            'device_id': self.device.id,
            'employee_id': emp.id,
        })
        res = wizard.action_confirm_user_management()
        mock_delete.assert_called_once_with(emp)
        self.assertEqual(res['type'], 'ir.actions.client')
