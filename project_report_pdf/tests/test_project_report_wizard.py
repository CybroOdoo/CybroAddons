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
import io
import json
import zipfile
from unittest.mock import MagicMock

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestProjectReportWizard(TransactionCase):
    """Tests the print actions and the XLSX export of the report wizard."""

    @classmethod
    def setUpClass(cls):
        """Create a project with two tasks in different stages."""
        super().setUpClass()
        cls.demo_user = new_test_user(
            cls.env, login='report_test_user', groups='base.group_user')
        cls.portal_user = new_test_user(
            cls.env, login='report_portal_user', groups='base.group_portal')
        cls.admin_user = cls.env.ref('base.user_admin')
        # without a document layout, Odoo asks an admin to configure it first
        cls.env.company.external_report_layout_id = cls.env.ref(
            'web.external_layout_standard')
        cls.project = cls.env['project.project'].create({
            'name': 'Test Project Alpha',
            'user_id': cls.admin_user.id,
        })
        cls.stage_open = cls.env['project.task.type'].create(
            {'name': 'In Progress'})
        cls.stage_done = cls.env['project.task.type'].create({'name': 'Done'})
        cls.env['project.task'].create({
            'name': 'Task One',
            'project_id': cls.project.id,
            'user_ids': [(4, cls.demo_user.id)],
            'stage_id': cls.stage_open.id,
        })
        cls.env['project.task'].create({
            'name': 'Task Two',
            'project_id': cls.project.id,
            'user_ids': [(4, cls.admin_user.id)],
            'stage_id': cls.stage_done.id,
        })

    def _wizard(self, user=None, **vals):
        """Open the wizard from the project form, as the given user."""
        model = self.env['project.report']
        if user:
            model = model.with_user(user)
        return model.with_context(active_id=self.project.id).create(vals)

    def _xlsx_strings(self, data):
        """Run the XLSX export and return the texts of the spreadsheet."""
        response = MagicMock()
        response.stream = io.BytesIO()
        self.env['project.report'].get_xlsx_report(data, response)
        with zipfile.ZipFile(io.BytesIO(response.stream.getvalue())) as xlsx:
            return xlsx.read('xl/sharedStrings.xml').decode()

    def test_project_defaults_to_active_project(self):
        """The wizard is linked to the project it is opened from."""
        self.assertEqual(self._wizard().project_id, self.project)

    def test_print_pdf_action(self):
        """Print PDF returns the PDF report action with the filters."""
        wizard = self._wizard(stage_ids=[(6, 0, [self.stage_open.id])])
        action = wizard.print_project_report_pdf()
        self.assertEqual(action['type'], 'ir.actions.report')
        self.assertEqual(
            action['report_name'], 'project_report_pdf.report_project_project')
        self.assertTrue(action['close_on_report_download'])
        self.assertEqual(action['data'], {
            'project_id': self.project.id,
            'user_ids': [],
            'stage_ids': [self.stage_open.id],
        })

    def test_print_xls_action(self):
        """Print XLS returns an XLSX report action with JSON options."""
        wizard = self._wizard(user_ids=[(6, 0, [self.demo_user.id])])
        action = wizard.print_project_report_xls()
        self.assertEqual(action['report_type'], 'xlsx')
        self.assertEqual(action['data']['output_format'], 'xlsx')
        self.assertEqual(json.loads(action['data']['options']), {
            'project_id': self.project.id,
            'user_ids': [self.demo_user.id],
            'stage_ids': [],
        })

    def test_xlsx_lists_all_tasks(self):
        """Without filters the spreadsheet lists every task."""
        strings = self._xlsx_strings({'project_id': self.project.id})
        self.assertIn('Test Project Alpha', strings)
        self.assertIn('Task One', strings)
        self.assertIn('Task Two', strings)

    def test_xlsx_applies_filters(self):
        """The spreadsheet only lists the tasks matching the filters."""
        strings = self._xlsx_strings({
            'project_id': self.project.id,
            'user_ids': [self.demo_user.id],
            'stage_ids': [self.stage_open.id],
        })
        self.assertIn('Task One', strings)
        self.assertNotIn('Task Two', strings)
        strings = self._xlsx_strings({
            'project_id': self.project.id,
            'stage_ids': [self.stage_done.id],
        })
        self.assertIn('Task Two', strings)
        self.assertNotIn('Task One', strings)

    def test_xlsx_without_project(self):
        """The export still produces a spreadsheet without a project."""
        strings = self._xlsx_strings({})
        self.assertIn('Tasks', strings)
        self.assertNotIn('Task One', strings)

    def test_internal_user_can_print(self):
        """A plain internal user can open the wizard and print."""
        wizard = self._wizard(user=self.demo_user)
        action = wizard.print_project_report_pdf()
        self.assertEqual(action['data']['project_id'], self.project.id)

    def test_portal_user_cannot_print(self):
        """A portal user has no access to the wizard."""
        with self.assertRaises(AccessError):
            self._wizard(user=self.portal_user)
