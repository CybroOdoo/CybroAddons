# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
from datetime import date, datetime

from odoo.tests import TransactionCase, new_test_user


class HrLeaveDashboardCommon(TransactionCase):
    """Shared fixture: a manager with two subordinates in one department.

    Time is frozen by the tests on Wednesday 17 June 2026, so "this week" is
    15-21 June and "this month" is June 2026.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.tz = 'UTC'
        cls.department = cls.env['hr.department'].create({
            'name': 'Dashboard Department',
        })
        cls.work_entry_type = cls.env['hr.work.entry.type'].create({
            'name': 'Dashboard Leave',
            'code': 'DASHLEAVE',
            'requires_allocation': False,
            'request_unit': 'day',
            'unit_of_measure': 'day',
            'leave_validation_type': 'hr',
        })
        cls.manager_user = new_test_user(
            cls.env, login='dash_manager', tz='UTC',
            groups='base.group_user,hr_holidays.group_hr_holidays_manager')
        cls.employee_user = new_test_user(
            cls.env, login='dash_employee', tz='UTC', groups='base.group_user')
        cls.no_employee_user = new_test_user(
            cls.env, login='dash_no_employee', tz='UTC',
            groups='base.group_user,hr_holidays.group_hr_holidays_manager')
        cls.manager = cls.env['hr.employee'].create({
            'name': 'Dash Manager',
            'user_id': cls.manager_user.id,
            'department_id': cls.department.id,
            'work_email': 'manager@example.com',
            'work_phone': '+1 555 0100',
            'tz': 'UTC',
            # 1x1 transparent PNG
            'image_1920': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
                          '+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
        })
        cls.employee_a = cls.env['hr.employee'].create({
            'name': 'Dash Employee A',
            'user_id': cls.employee_user.id,
            'parent_id': cls.manager.id,
            'department_id': cls.department.id,
            'tz': 'UTC',
        })
        cls.employee_b = cls.env['hr.employee'].create({
            'name': 'Dash Employee B',
            'parent_id': cls.manager.id,
            'department_id': cls.department.id,
            'tz': 'UTC',
        })

    def _create_leave(self, employee, date_from, date_to=None, state='validate'):
        """Create a day leave and bring it to ``state``
        (``confirm``, ``validate`` or ``refuse``)."""
        leave = self.env['hr.leave'].with_context(tracking_disable=True).create({
            'name': 'Dashboard leave',
            'employee_id': employee.id,
            'work_entry_type_id': self.work_entry_type.id,
            'request_date_from': date_from,
            'request_date_to': date_to or date_from,
        })
        if state == 'confirm':
            leave.state = 'confirm'
        elif state == 'validate' and leave.state != 'validate':
            leave.action_approve()
        elif state == 'refuse':
            if leave.state != 'validate':
                leave.action_approve()
            leave.action_refuse()
        self.assertEqual(leave.state, state)
        return leave

    def _create_public_holiday(self, name, date_from, date_to, company=None):
        """Create a company-wide public holiday (UTC datetimes)."""
        return self.env['resource.calendar.leaves'].create({
            'name': name,
            'date_from': date_from,
            'date_to': date_to,
            'company_id': (company or self.company).id,
        })


TODAY = date(2026, 6, 17)
NOW = datetime(2026, 6, 17, 10, 0)
