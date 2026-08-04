# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestHrAnnouncement(TransactionCase):

    def setUp(self):
        super().setUp()

        self.hr_announcement = self.env['hr.announcement']
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Employee',
        })
        self.department = self.env['hr.department'].create({
            'name': 'Test Department',
        })
        self.job = self.env['hr.job'].create({
            'name': 'Test Job Position',
        })

    def test_01_create_general_announcement(self):
        """Test creation of general announcement."""
        announcement = self.hr_announcement.create({
            'announcement_reason': 'General Meeting',
            'is_announcement': True,
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=5),
        })

        self.assertEqual(announcement.name[:2], 'GA')
        self.assertEqual(announcement.state, 'draft')

    def test_02_create_employee_specific_announcement(self):
        """Test announcement targeted to specific employee."""
        announcement = self.hr_announcement.create({
            'announcement_reason': 'Salary Update',
            'announcement_type': 'employee',
            'employee_ids': [(6, 0, [self.employee.id])],
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=3),
        })

        self.assertEqual(announcement.announcement_type, 'employee')
        self.assertIn(self.employee, announcement.employee_ids)

    def test_03_create_department_announcement(self):
        """Test announcement targeted to department."""
        announcement = self.hr_announcement.create({
            'announcement_reason': 'Department Meeting',
            'announcement_type': 'department',
            'department_ids': [(6, 0, [self.department.id])],
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=3),
        })

        self.assertEqual(announcement.announcement_type, 'department')

    def test_04_date_validation(self):
        """Test date constraint (start date < end date)."""
        with self.assertRaises(ValidationError):
            self.hr_announcement.create({
                'announcement_reason': 'Invalid Dates',
                'date_start': date.today() + timedelta(days=5),
                'date_end': date.today(),
            })

    def test_05_approval_workflow(self):
        """Test announcement approval workflow."""
        announcement = self.hr_announcement.create({
            'announcement_reason': 'Policy Change',
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=10),
        })

        announcement.action_send()
        self.assertEqual(announcement.state, 'to_approve')

        announcement.action_approve()
        self.assertEqual(announcement.state, 'approved')

        announcement.action_reject()
        self.assertEqual(announcement.state, 'rejected')

    def test_06_expiry_cron(self):
        """Test automatic expiry via cron."""
        announcement = self.hr_announcement.create({
            'announcement_reason': 'Expired Announcement',
            'date_start': date.today() - timedelta(days=10),
            'date_end': date.today() - timedelta(days=1),
            'state': 'approved',
        })

        # Simulate cron job
        self.hr_announcement.get_expiry_state()

        self.assertEqual(announcement.state, 'expired')

    def test_07_employee_announcement_count(self):
        """Test announcement count on employee form."""
        self.hr_announcement.create({
            'announcement_reason': 'Test Count',
            'is_announcement': True,
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=5),
            'state': 'approved',
        })

        self.employee._compute_announcement_count()
        self.assertGreaterEqual(self.employee.announcement_count, 1)

    def test_08_sequence_generation(self):
        """Test sequence number generation."""
        general = self.hr_announcement.create({
            'announcement_reason': 'General',
            'is_announcement': True,
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=1),
        })

        specific = self.hr_announcement.create({
            'announcement_reason': 'Specific',
            'date_start': date.today(),
            'date_end': date.today() + timedelta(days=1),
        })

        self.assertTrue(general.name.startswith('GA'))
        self.assertTrue(specific.name.startswith('AN'))
