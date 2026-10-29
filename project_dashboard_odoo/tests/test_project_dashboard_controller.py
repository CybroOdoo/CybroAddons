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
#############################################################################
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, new_test_user, tagged

from odoo.addons.project_dashboard_odoo.controllers import project_dashboard_odoo
from odoo.addons.project_dashboard_odoo.controllers.project_dashboard_odoo import (
    ProjectFilter,
)


@tagged('post_install', '-at_install')
class TestProjectDashboardController(TransactionCase):
    """Test suite for Project Dashboard controller endpoints and helpers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = ProjectFilter()

        # Create Manager User
        cls.manager_user = new_test_user(
            cls.env,
            login='proj_manager_user',
            groups='project.group_project_manager,hr_timesheet.group_hr_timesheet_user',
            name='Project Manager User',
        )

        # Create Regular Project User
        cls.regular_user = new_test_user(
            cls.env,
            login='proj_regular_user',
            groups='project.group_project_user',
            name='Regular Project User',
        )

        # Set up company and records
        cls.company = cls.env.company
        cls.project = cls.env['project.project'].create({
            'name': 'Alpha Test Project',
            'user_id': cls.regular_user.id,
            'company_id': cls.company.id,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Alpha Test Task',
            'project_id': cls.project.id,
            'user_ids': [cls.regular_user.id],
        })
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Alice Employee',
            'company_id': cls.company.id,
            'user_id': cls.manager_user.id,
        })

    def _get_mock_request(self, user=None, company=None):
        """Construct a mock request object for controller method execution."""
        mock = MagicMock()
        target_user = user or self.env.user
        target_company = company or self.company
        target_env = self.env(user=target_user, context={'allowed_company_ids': [target_company.id]})
        mock.env = target_env
        mock.cookies = {'cids': str(target_company.id)}
        mock.update_context = MagicMock()
        return mock

    def test_init_request_context(self):
        """Verify _init_request_context extracts and sets company IDs."""
        mock_req = self._get_mock_request()
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            self.controller._init_request_context(context={'allowed_company_ids': [self.company.id]})
            mock_req.update_context.assert_called_with(allowed_company_ids=[self.company.id])

    def test_get_project_task_count(self):
        """Verify /project/task/count returns projects, task counts, and colors."""
        mock_req = self._get_mock_request(user=self.manager_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            res = self.controller.get_project_task_count()
            self.assertIn('project', res)
            self.assertIn('task', res)
            self.assertIn('color', res)
            self.assertIn(self.project.name, res['project'])
            idx = res['project'].index(self.project.name)
            self.assertGreaterEqual(res['task'][idx], 1)
            self.assertTrue(res['color'][idx].startswith('#'))

    def test_get_top_timesheet_employees(self):
        """Verify /employee/timesheet returns unit amounts and employee names."""
        mock_req = self._get_mock_request(user=self.manager_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            res = self.controller.get_top_timesheet_employees()
            self.assertIsInstance(res, list)
            self.assertEqual(len(res), 2)
            self.assertIsInstance(res[0], list)
            self.assertIsInstance(res[1], list)

    def test_project_filter(self):
        """Verify /project/filter returns project and employee selection data."""
        mock_req = self._get_mock_request(user=self.manager_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            res = self.controller.project_filter()
            self.assertEqual(len(res), 2)
            project_list, employee_list = res
            self.assertTrue(any(p['id'] == self.project.id for p in project_list))
            self.assertTrue(any(e['id'] == self.employee.id for e in employee_list))

    def test_get_tiles_data_manager(self):
        """Verify /get/tiles/data returns complete KPI data for managers (flag=1)."""
        mock_req = self._get_mock_request(user=self.manager_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            res = self.controller.get_tiles_data()
            self.assertEqual(res['flag'], 1)
            self.assertIn('total_projects', res)
            self.assertIn('total_tasks', res)
            self.assertIn('total_hours', res)
            self.assertIn('total_profitability', res)
            self.assertIn('total_employees', res)
            self.assertIn('total_sale_orders', res)
            self.assertIn('project_stage_list', res)
            self.assertIn('currency_symbol', res)
            self.assertGreaterEqual(res['total_projects'], 1)

    def test_get_tiles_data_regular_user(self):
        """Verify /get/tiles/data returns restricted view for non-managers (flag=2)."""
        mock_req = self._get_mock_request(user=self.regular_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            res = self.controller.get_tiles_data()
            self.assertEqual(res['flag'], 2)
            self.assertIn('total_projects', res)
            self.assertIn('total_tasks', res)
            self.assertEqual(res['total_employees'], 0)

    def test_get_hours_data(self):
        """Verify /get/hours returns expected hour breakdown keys."""
        mock_req = self._get_mock_request(user=self.manager_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            res = self.controller.get_hours_data()
            for key in ['hour_recorded', 'hour_recorde', 'billable_fix', 'non_billable', 'total_hr']:
                self.assertIn(key, res)
                self.assertIsInstance(res[key], list)

    def test_get_task_data(self):
        """Verify /get/task/data returns tabular task info for manager and regular user."""
        mock_req = self._get_mock_request(user=self.manager_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            res = self.controller.get_task_data()
            self.assertIn('project', res)
            task_entries = [entry for entry in res['project'] if entry[1] == self.task.id]
            self.assertTrue(task_entries)
            self.assertEqual(task_entries[0][0], self.task.name)
            self.assertEqual(task_entries[0][2], self.project.name)

        # Test regular user branch
        mock_user_req = self._get_mock_request(user=self.regular_user)
        with patch.object(project_dashboard_odoo, 'request', mock_user_req):
            res_user = self.controller.get_task_data()
            self.assertIn('project', res_user)

    def test_project_filter_apply(self):
        """Verify /project/filter-apply correctly aggregates filtered data."""
        mock_req = self._get_mock_request(user=self.manager_user)
        with patch.object(project_dashboard_odoo, 'request', mock_req):
            filter_data = {
                'data': {
                    'project': str(self.project.id),
                    'employee': str(self.employee.id),
                    'start_date': '2026-01-01',
                    'end_date': '2026-12-31',
                },
            }
            res = self.controller.project_filter_apply(**filter_data)
            self.assertIn('total_project', res)
            self.assertIn('total_emp', res)
            self.assertIn('total_task', res)
            self.assertIn('hours_recorded', res)
            self.assertIn('total_margin', res)
            self.assertIn('total_so', res)
            self.assertEqual(res['total_project'], [self.project.id])
            self.assertEqual(res['total_emp'], [self.employee.id])
