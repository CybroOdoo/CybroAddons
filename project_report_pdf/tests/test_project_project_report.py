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
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestReportProjectProjectPdf(TransactionCase):
    """Tests the values and the rendering of the project PDF report."""

    @classmethod
    def setUpClass(cls):
        """Create a project with two tasks in different stages."""
        super().setUpClass()
        cls.report_model = cls.env[
            'report.project_report_pdf.report_project_project'
        ]
        cls.demo_user = new_test_user(
            cls.env, login='report_test_user', groups='base.group_user')
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.project = cls.env['project.project'].create({
            'name': 'Report Test Project',
            'user_id': cls.admin_user.id,
        })
        cls.stage_todo = cls.env['project.task.type'].create({'name': 'To Do'})
        cls.stage_done = cls.env['project.task.type'].create({'name': 'Done'})
        cls.task_1 = cls.env['project.task'].create({
            'name': 'Report Task One',
            'project_id': cls.project.id,
            'user_ids': [(6, 0, [cls.demo_user.id])],
            'stage_id': cls.stage_todo.id,
        })
        cls.task_2 = cls.env['project.task'].create({
            'name': 'Report Task Two',
            'project_id': cls.project.id,
            'user_ids': [(6, 0, [cls.admin_user.id])],
            'stage_id': cls.stage_done.id,
        })

    def _report_values(self, user_ids=None, stage_ids=None, project=None):
        """Return the report values of a wizard with the given filters."""
        wizard = self.env['project.report'].create({
            'project_id': (project or self.project).id,
            'user_ids': [(6, 0, user_ids or [])],
            'stage_ids': [(6, 0, stage_ids or [])],
        })
        return self.report_model._get_report_values(
            wizard.ids, data=wizard._get_report_data())

    def _task_names(self, values):
        """Return the task names listed in the report values."""
        return [line['name'] for line in values['vals']]

    def test_project_header(self):
        """The report shows the project name and its manager."""
        values = self._report_values()
        self.assertEqual(values['name'], 'Report Test Project')
        self.assertEqual(values['manager'], self.admin_user.name)
        self.assertEqual(values['docs'], self.project)

    def test_no_filters_returns_all_tasks(self):
        """Without filters every task of the project is listed."""
        self.assertCountEqual(
            self._task_names(self._report_values()),
            ['Report Task One', 'Report Task Two'])

    def test_assignee_filter(self):
        """Only the tasks of the selected assignees are listed."""
        values = self._report_values(user_ids=[self.demo_user.id])
        self.assertEqual(self._task_names(values), ['Report Task One'])
        values = self._report_values(
            user_ids=[self.demo_user.id, self.admin_user.id])
        self.assertCountEqual(
            self._task_names(values), ['Report Task One', 'Report Task Two'])

    def test_stage_filter(self):
        """Only the tasks in the selected stages are listed."""
        values = self._report_values(stage_ids=[self.stage_done.id])
        self.assertEqual(self._task_names(values), ['Report Task Two'])
        self.assertEqual(values['vals'][0]['stage_id'], 'Done')

    def test_both_filters(self):
        """Assignee and stage filters are combined."""
        values = self._report_values(
            user_ids=[self.demo_user.id], stage_ids=[self.stage_todo.id])
        self.assertEqual(self._task_names(values), ['Report Task One'])
        values = self._report_values(
            user_ids=[self.demo_user.id], stage_ids=[self.stage_done.id])
        self.assertEqual(values['vals'], [])

    def test_empty_project(self):
        """A project without tasks gives an empty task list."""
        empty_project = self.env['project.project'].create({
            'name': 'Empty Project',
        })
        values = self._report_values(project=empty_project)
        self.assertEqual(values['name'], 'Empty Project')
        self.assertEqual(values['vals'], [])

    def test_values_from_wizard_without_data(self):
        """Without report data the filters are read from the wizard."""
        wizard = self.env['project.report'].create({
            'project_id': self.project.id,
            'stage_ids': [(6, 0, [self.stage_todo.id])],
        })
        values = self.report_model._get_report_values(wizard.ids)
        self.assertEqual(self._task_names(values), ['Report Task One'])

    def test_multiple_assignees_are_joined(self):
        """The names of several assignees are joined with a comma."""
        self.task_1.user_ids = [(6, 0, [self.demo_user.id, self.admin_user.id])]
        line = self._report_values(stage_ids=[self.stage_todo.id])['vals'][0]
        self.assertEqual(
            line['user_id'],
            ', '.join(self.task_1.user_ids.mapped('name')))

    def test_get_task_lines_without_project(self):
        """Without a project there are no task lines."""
        self.assertEqual(self.env['project.report']._get_task_lines(False), [])

    def test_html_report_renders_tasks(self):
        """The QWeb template renders the project and its filtered tasks."""
        wizard = self.env['project.report'].create({
            'project_id': self.project.id,
            'stage_ids': [(6, 0, [self.stage_todo.id])],
        })
        report = self.env.ref(
            'project_report_pdf.action_report_project_project')
        html, _fmt = report._render_qweb_html(
            report.report_name, wizard.ids, data=wizard._get_report_data())
        self.assertIn(b'Report Test Project', html)
        self.assertIn(b'Report Task One', html)
        self.assertNotIn(b'Report Task Two', html)
