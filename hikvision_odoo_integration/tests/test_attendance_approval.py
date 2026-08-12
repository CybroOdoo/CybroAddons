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
from datetime import datetime, date
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError, AccessError, ValidationError


@tagged('post_install', '-at_install')
class TestAttendanceApproval(TransactionCase):
    """Test suite for Attendance Approval model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_manager_user = cls.env['res.users'].create({
            'name': 'HR Manager User',
            'login': 'hrmanager@example.com',
            'email': 'hrmanager@example.com',
            'groups_id': [(6, 0, [cls.env.ref('hr.group_hr_manager').id, cls.env.ref('base.group_user').id])],
        })
        cls.normal_user = cls.env['res.users'].create({
            'name': 'Normal Employee User',
            'login': 'normaluser@example.com',
            'email': 'normaluser@example.com',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'work_email': 'testemp@example.com',
            'user_id': cls.normal_user.id,
        })
        cls.today = fields_date = date.today()
        cls.approval = cls.env['attendance.approval'].create({
            'employee_id': cls.employee.id,
            'date': cls.today,
            'reason': 'Traffic delay',
        })

    def test_compute_total_hours(self):
        """Test total hours computation for employee on a given date."""
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': datetime.combine(self.today, datetime.min.time()).replace(hour=9),
            'check_out': datetime.combine(self.today, datetime.min.time()).replace(hour=14), # 5 hours
        })
        self.approval._compute_total_hours()
        self.assertEqual(self.approval.total_hours, 5.0)

    def test_action_submit_missing_reason(self):
        """Test error raised when submitting approval without a reason."""
        approval_no_reason = self.env['attendance.approval'].create({
            'employee_id': self.employee.id,
            'date': self.today,
        })
        with self.assertRaises(UserError):
            approval_no_reason.action_submit()

    def test_action_submit_success(self):
        """Test successful submission of attendance approval."""
        self.approval.action_submit()
        self.assertEqual(self.approval.state, 'submitted')
        activity = self.env['mail.activity'].search([
            ('res_id', '=', self.approval.id),
            ('res_model', '=', 'attendance.approval')
        ], limit=1)
        self.assertTrue(activity.exists())

    def test_action_approve_as_hr_manager(self):
        """Test approval by HR manager."""
        self.approval.action_submit()
        res = self.approval.with_user(self.hr_manager_user).action_approve()
        self.assertEqual(self.approval.state, 'approved')

    def test_action_approve_as_normal_user(self):
        """Test access restriction for non-HR manager users."""
        self.approval.action_submit()
        with self.assertRaises(AccessError):
            self.approval.with_user(self.normal_user).action_approve()

    def test_action_reject_as_hr_manager(self):
        """Test rejection wizard action returned for HR manager."""
        self.approval.action_submit()
        action = self.approval.with_user(self.hr_manager_user).action_reject()
        self.assertEqual(action['res_model'], 'attendance.rejection.wizard')
        self.assertEqual(action['context']['default_approval_id'], self.approval.id)

    def test_action_reject_as_normal_user(self):
        """Test rejection access restriction for non-HR manager users."""
        self.approval.action_submit()
        with self.assertRaises(AccessError):
            self.approval.with_user(self.normal_user).action_reject()

    def test_cron_check_attendance_approvals(self):
        """Test cron job creating draft approvals when HR approval parameter is enabled."""
        # Enable HR approval parameter
        self.env['ir.config_parameter'].sudo().set_param('hikvision_odoo_integration.enable_hr_approval', 'True')
        self.env['ir.config_parameter'].sudo().set_param('hikvision_odoo_integration.minimum_working_hours', '8.0')

        # Employee working only 4 hours
        emp_shortfall = self.env['hr.employee'].create({
            'name': 'Shortfall Employee',
            'work_email': 'shortfall@example.com'
        })
        self.env['hr.attendance'].create({
            'employee_id': emp_shortfall.id,
            'check_in': datetime.combine(self.today, datetime.min.time()).replace(hour=9),
            'check_out': datetime.combine(self.today, datetime.min.time()).replace(hour=13),
        })

        self.env['attendance.approval'].cron_check_attendance_approvals()

        approval_created = self.env['attendance.approval'].search([
            ('employee_id', '=', emp_shortfall.id),
            ('date', '=', self.today)
        ], limit=1)
        self.assertTrue(approval_created.exists())
        self.assertEqual(approval_created.state, 'draft')
