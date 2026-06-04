# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from odoo.tests.common import TransactionCase


class TestReportProjectProjectPdf(TransactionCase):
    """Test suite for report/project_project_report.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env[
            'report.project_report_pdf.report_project_project'
        ]
        cls.demo_user = cls.env.ref('base.user_demo')
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

    def _make_wizard(self, partner_select=None, stage_select=None):
        vals = {}
        if partner_select:
            vals['partner_select'] = [(4, uid) for uid in partner_select]
        if stage_select:
            vals['stage_select'] = [(4, sid) for sid in stage_select]
        return self.env['project.report'].create(vals)

    # -------------------------------------------------------------------------
    # No filters — all tasks returned
    # -------------------------------------------------------------------------

    def test_no_filters_returns_all_tasks(self):
        """With no filter, all project tasks should appear in vals."""
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        task_names = [v['name'] for v in result['vals']]
        self.assertIn('Report Task One', task_names)
        self.assertIn('Report Task Two', task_names)

    def test_result_contains_project_name(self):
        """Result should contain the correct project name."""
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        self.assertEqual(result['name'], 'Report Test Project')

    def test_result_contains_manager_name(self):
        """Result should contain the project manager's name."""
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        self.assertEqual(result['manager'], self.admin_user.name)

    def test_result_contains_date_keys(self):
        """Result should always include date_start and date_end keys."""
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        self.assertIn('date_start', result)
        self.assertIn('date_end', result)

    def test_vals_task_has_required_keys(self):
        """Each entry in vals should have 'name', 'user_id', and 'stage_id'."""
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        for entry in result['vals']:
            self.assertIn('name', entry)
            self.assertIn('user_id', entry)
            self.assertIn('stage_id', entry)

    def test_vals_user_id_is_string(self):
        """user_id in each val entry should be a string."""
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        for entry in result['vals']:
            self.assertIsInstance(entry['user_id'], str)

    def test_vals_stage_id_is_string(self):
        """stage_id in each val entry should be the stage name string."""
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        for entry in result['vals']:
            self.assertIsInstance(entry['stage_id'], str)

    # -------------------------------------------------------------------------
    # Partner filter only
    # -------------------------------------------------------------------------

    def test_partner_filter_restricts_tasks(self):
        """With only partner filter, only tasks assigned to that user should appear."""
        self._make_wizard(partner_select=[self.demo_user.id])
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        task_names = [v['name'] for v in result['vals']]
        self.assertIn('Report Task One', task_names)
        self.assertNotIn('Report Task Two', task_names)

    def test_partner_filter_multiple_users(self):
        """With multiple users selected, tasks for both should appear."""
        self._make_wizard(partner_select=[self.demo_user.id, self.admin_user.id])
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        task_names = [v['name'] for v in result['vals']]
        self.assertIn('Report Task One', task_names)
        self.assertIn('Report Task Two', task_names)

    # -------------------------------------------------------------------------
    # Stage filter only
    # -------------------------------------------------------------------------

    def test_stage_filter_restricts_tasks(self):
        """With only stage filter, only tasks in that stage should appear."""
        self._make_wizard(stage_select=[self.stage_todo.id])
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        task_names = [v['name'] for v in result['vals']]
        self.assertIn('Report Task One', task_names)
        self.assertNotIn('Report Task Two', task_names)

    def test_stage_filter_done_stage(self):
        """Stage filter for 'Done' should return only done tasks."""
        self._make_wizard(stage_select=[self.stage_done.id])
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        task_names = [v['name'] for v in result['vals']]
        self.assertIn('Report Task Two', task_names)
        self.assertNotIn('Report Task One', task_names)

    # -------------------------------------------------------------------------
    # Both filters combined
    # -------------------------------------------------------------------------

    def test_both_filters_match(self):
        """Both filters matching should return the intersection."""
        self._make_wizard(
            partner_select=[self.demo_user.id],
            stage_select=[self.stage_todo.id],
        )
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        task_names = [v['name'] for v in result['vals']]
        self.assertIn('Report Task One', task_names)
        self.assertNotIn('Report Task Two', task_names)

    def test_both_filters_no_match(self):
        """Both filters with no intersection should return an empty vals list."""
        self._make_wizard(
            partner_select=[self.demo_user.id],
            stage_select=[self.stage_done.id],
        )
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        # demo_user has no task in stage_done
        self.assertEqual(result['vals'], [])

    # -------------------------------------------------------------------------
    # Empty task set fallback
    # -------------------------------------------------------------------------

    def test_empty_task_result_returns_dict(self):
        """When no tasks match, result should still be a dict."""
        empty_project = self.env['project.project'].create({
            'name': 'Empty Project',
            'user_id': self.admin_user.id,
        })
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': empty_project.id}
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(result['vals'], [])

    def test_empty_task_result_has_name_key(self):
        """Even with no tasks, result should include the 'name' key."""
        empty_project = self.env['project.project'].create({
            'name': 'Empty Project B',
            'user_id': self.admin_user.id,
        })
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': empty_project.id}
        )
        self.assertIn('name', result)

    # -------------------------------------------------------------------------
    # Multi-assignee formatting
    # -------------------------------------------------------------------------

    def test_multi_assignee_joined_with_comma(self):
        """Tasks with multiple assignees should have names joined by ' , '."""
        multi_task = self.env['project.task'].create({
            'name': 'Multi Assignee Task',
            'project_id': self.project.id,
            'user_ids': [(6, 0, [self.demo_user.id, self.admin_user.id])],
            'stage_id': self.stage_todo.id,
        })
        self._make_wizard()
        result = self.report_model._get_report_values(
            [], data={'record': self.project.id}
        )
        entry = next(
            (v for v in result['vals'] if v['name'] == 'Multi Assignee Task'),
            None,
        )
        self.assertIsNotNone(entry)
        self.assertIn(' , ', entry['user_id'])
        multi_task.unlink()
