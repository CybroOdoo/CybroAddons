# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from os.path import exists, join

from odoo.modules.module import get_module_path
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAttendanceCalendarView(TransactionCase):
    """Test suite for Attendance View Calendar module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_path = get_module_path('attendance_view_calendar')

    def test_01_module_installed(self):
        """Verify attendance_view_calendar module is installed."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'attendance_view_calendar')], limit=1
        )
        self.assertTrue(module, 'Module record not found')
        self.assertEqual(
            module.state, 'installed', 'Module should be in installed state'
        )

    def test_02_manifest_metadata(self):
        """Verify manifest metadata meets checklist standards."""
        module = self.env['ir.module.module'].search(
            [('name', '=', 'attendance_view_calendar')], limit=1
        )
        self.assertEqual(module.license, 'LGPL-3')
        self.assertIn(
            module.category_id.name,
            ('Human Resources', 'Attendances'),
        )
        self.assertIn(
            'hr_attendance', module.dependencies_id.mapped('name')
        )
        self.assertIn(
            'hr_attendance_gantt', module.dependencies_id.mapped('name')
        )

    def test_03_calendar_view_definition(self):
        """Verify calendar view is defined for hr.attendance with start/stop.
        """
        view = self.env.ref(
            'attendance_view_calendar.hr_attendance_view_calendar',
            raise_if_not_found=False,
        )
        self.assertIsNotNone(view, 'Calendar view reference must exist')
        self.assertEqual(view.model, 'hr.attendance')
        self.assertEqual(view.type, 'calendar')
        arch = view.arch
        self.assertIn('date_start="check_in"', arch)
        self.assertIn('date_stop="check_out"', arch)
        self.assertIn('employee_id', arch)

    def test_04_action_view_mode(self):
        """Verify hr_attendance_action view_mode includes calendar."""
        action = self.env.ref(
            'hr_attendance.hr_attendance_action',
            raise_if_not_found=False,
        )
        self.assertIsNotNone(action, 'hr_attendance_action must exist')
        modes = [
            m.strip()
            for m in (action.view_mode or '').split(',')
            if m.strip()
        ]
        self.assertIn(
            'calendar',
            modes,
            'Action view_mode should include calendar view',
        )

    def test_05_docs_and_assets(self):
        """Verify required documentation and asset files exist."""
        required_relative_paths = [
            'README.rst',
            join('doc', 'RELEASE_NOTES.md'),
            join('static', 'description', 'icon.png'),
            join('static', 'description', 'banner.jpg'),
            join('static', 'description', 'index.html'),
        ]
        for rel_path in required_relative_paths:
            full_path = join(self.module_path, rel_path)
            self.assertTrue(
                exists(full_path), f'Missing required file: {rel_path}'
            )

        for i in range(1, 7):
            screenshot = join(
                self.module_path,
                'static',
                'description',
                'assets',
                'screenshots',
                f'{i}.png',
            )
            self.assertTrue(
                exists(screenshot), f'Missing screenshot {i}.png'
            )

    def test_06_attendance_calendar_data(self):
        """Verify attendance records can be created with check_in/check_out."""
        employee = self.env['hr.employee'].create({
            'name': 'Test Calendar Employee',
        })
        attendance = self.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': '2026-10-27 09:00:00',
            'check_out': '2026-10-27 17:00:00',
        })
        self.assertTrue(attendance.id)
        self.assertEqual(attendance.worked_hours, 8.0)
