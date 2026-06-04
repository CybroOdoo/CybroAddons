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
import io
import json
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase


class TestProjectReportWizard(TransactionCase):
    """Test suite for wizard/project_report.py — ProjectReport transient model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.demo_user = cls.env.ref('base.user_demo')
        cls.admin_user = cls.env.ref('base.user_admin')

        cls.project = cls.env['project.project'].create({
            'name': 'Test Project Alpha',
            'user_id': cls.admin_user.id,
        })
        cls.stage_open = cls.env['project.task.type'].create({'name': 'In Progress'})
        cls.stage_done = cls.env['project.task.type'].create({'name': 'Done'})

        cls.task_1 = cls.env['project.task'].create({
            'name': 'Task One',
            'project_id': cls.project.id,
            'user_ids': [(4, cls.demo_user.id)],
            'stage_id': cls.stage_open.id,
        })
        cls.task_2 = cls.env['project.task'].create({
            'name': 'Task Two',
            'project_id': cls.project.id,
            'user_ids': [(4, cls.admin_user.id)],
            'stage_id': cls.stage_done.id,
        })

    def _wizard(self, partner_select=None, stage_select=None):
        """Create wizard and return it with active_id in context.
        """
        vals = {}
        if partner_select:
            vals['partner_select'] = [(4, uid) for uid in partner_select]
        if stage_select:
            vals['stage_select'] = [(4, sid) for sid in stage_select]
        ctx = {'active_id': self.project.id}
        wizard = self.env['project.report'].with_context(ctx).create(vals)
        return wizard.with_context(ctx)

    # -------------------------------------------------------------------------
    # Model / field tests
    # -------------------------------------------------------------------------

    def test_wizard_create_no_filters(self):
        """Wizard should be creatable with no partner or stage selection."""
        wizard = self._wizard()
        self.assertFalse(wizard.partner_select)
        self.assertFalse(wizard.stage_select)

    def test_wizard_partner_select_field(self):
        """partner_select (Many2many res.users) should accept user records."""
        wizard = self._wizard(partner_select=[self.demo_user.id])
        self.assertIn(self.demo_user, wizard.partner_select)

    def test_wizard_stage_select_field(self):
        """stage_select (Many2many project.task.type) should accept stage records."""
        wizard = self._wizard(stage_select=[self.stage_open.id])
        self.assertIn(self.stage_open, wizard.stage_select)

    def test_wizard_both_filters(self):
        """Wizard should accept both partner and stage filters simultaneously."""
        wizard = self._wizard(
            partner_select=[self.demo_user.id],
            stage_select=[self.stage_open.id],
        )
        self.assertIn(self.demo_user, wizard.partner_select)
        self.assertIn(self.stage_open, wizard.stage_select)

    # -------------------------------------------------------------------------
    # print_project_report_pdf
    # -------------------------------------------------------------------------

    def test_print_pdf_returns_report_action(self):
        """print_project_report_pdf should return a dict."""
        wizard = self._wizard()
        mock_ref = MagicMock()
        mock_ref.report_action.return_value = {'type': 'ir.actions.report'}
        with patch.object(type(wizard.env), 'ref', return_value=mock_ref):
            result = wizard.with_context(active_id=self.project.id).print_project_report_pdf()
        self.assertIsInstance(result, dict)

    def test_print_pdf_sets_close_on_download(self):
        """print_project_report_pdf result should include close_on_report_download=True."""
        wizard = self._wizard()
        mock_ref = MagicMock()
        mock_ref.report_action.return_value = {'type': 'ir.actions.report'}
        with patch.object(type(wizard.env), 'ref', return_value=mock_ref):
            result = wizard.with_context(active_id=self.project.id).print_project_report_pdf()
        self.assertTrue(result.get('close_on_report_download'))

    def test_print_pdf_passes_record_id_in_data(self):
        """print_project_report_pdf should pass the project id in data['record']."""
        wizard = self._wizard()
        captured = {}

        mock_ref = MagicMock()
        mock_ref.report_action.side_effect = lambda records, data=None, **kw: (
            captured.update({'data': data}) or {'type': 'ir.actions.report'}
        )
        with patch.object(type(wizard.env), 'ref', return_value=mock_ref):
            wizard.with_context(active_id=self.project.id).print_project_report_pdf()

        self.assertEqual(captured.get('data', {}).get('record'), self.project.id)

    # -------------------------------------------------------------------------
    # print_project_report_xls
    # -------------------------------------------------------------------------

    def test_print_xls_returns_dict(self):
        """print_project_report_xls should return a dict."""
        wizard = self._wizard()
        result = wizard.with_context(active_id=self.project.id).print_project_report_xls()
        self.assertIsInstance(result, dict)

    def test_print_xls_report_type_xlsx(self):
        """print_project_report_xls result report_type should be 'xlsx'."""
        wizard = self._wizard()
        result = wizard.with_context(active_id=self.project.id).print_project_report_xls()
        self.assertEqual(result.get('report_type'), 'xlsx')

    def test_print_xls_data_contains_model(self):
        """print_project_report_xls data should include model='project.report'."""
        wizard = self._wizard()
        result = wizard.with_context(active_id=self.project.id).print_project_report_xls()
        self.assertEqual(result['data'].get('model'), 'project.report')

    def test_print_xls_data_output_format(self):
        """print_project_report_xls data output_format should be 'xlsx'."""
        wizard = self._wizard()
        result = wizard.with_context(active_id=self.project.id).print_project_report_xls()
        self.assertEqual(result['data'].get('output_format'), 'xlsx')

    def test_print_xls_data_options_is_json(self):
        """print_project_report_xls data options should be valid JSON."""
        wizard = self._wizard()
        result = wizard.with_context(active_id=self.project.id).print_project_report_xls()
        parsed = json.loads(result['data']['options'])
        self.assertIsInstance(parsed, dict)

    def test_print_xls_options_contains_record_id(self):
        """print_project_report_xls options JSON should contain the project id."""
        wizard = self._wizard()
        result = wizard.with_context(active_id=self.project.id).print_project_report_xls()
        options = json.loads(result['data']['options'])
        self.assertEqual(options.get('record'), self.project.id)

    def test_print_xls_report_name(self):
        """print_project_report_xls data report_name should be 'Project Report'."""
        wizard = self._wizard()
        result = wizard.with_context(active_id=self.project.id).print_project_report_xls()
        self.assertEqual(result['data'].get('report_name'), 'Project Report')

    # -------------------------------------------------------------------------
    # get_xlsx_report
    # -------------------------------------------------------------------------

    def _run_xlsx(self, wizard, data):
        """Run get_xlsx_report with request.env safely replaced by self.env."""
        response = MagicMock()
        response.stream = io.BytesIO()

        mock_request = MagicMock()
        mock_request.env = self.env   # real env, not a LocalProxy

        with patch.dict(
            'odoo.addons.project_report_pdf.wizard.project_report.__dict__',
            {'request': mock_request},
        ):
            wizard.get_xlsx_report(data, response)
        return response

    def test_get_xlsx_report_writes_bytes(self):
        """get_xlsx_report should write non-empty bytes to the response stream."""
        wizard = self._wizard()
        response = self._run_xlsx(wizard, {'record': self.project.id})
        response.stream.seek(0)
        self.assertGreater(len(response.stream.read()), 0)

    def test_get_xlsx_report_valid_xlsx_magic_bytes(self):
        """Output should start with the XLSX/ZIP magic bytes PK\\x03\\x04."""
        wizard = self._wizard()
        response = self._run_xlsx(wizard, {'record': self.project.id})
        response.stream.seek(0)
        self.assertEqual(response.stream.read(4), b'PK\x03\x04')

    def test_get_xlsx_report_with_partner_filter(self):
        """get_xlsx_report should succeed when a partner filter is active."""
        wizard = self._wizard(partner_select=[self.demo_user.id])
        response = self._run_xlsx(wizard, {'record': self.project.id})
        response.stream.seek(0)
        self.assertGreater(len(response.stream.read()), 0)

    def test_get_xlsx_report_with_stage_filter(self):
        """get_xlsx_report should succeed when a stage filter is active."""
        wizard = self._wizard(stage_select=[self.stage_open.id])
        response = self._run_xlsx(wizard, {'record': self.project.id})
        response.stream.seek(0)
        self.assertGreater(len(response.stream.read()), 0)

    def test_get_xlsx_report_with_both_filters(self):
        """get_xlsx_report should succeed with both filters active."""
        wizard = self._wizard(
            partner_select=[self.demo_user.id],
            stage_select=[self.stage_open.id],
        )
        response = self._run_xlsx(wizard, {'record': self.project.id})
        response.stream.seek(0)
        self.assertGreater(len(response.stream.read()), 0)

    def test_get_xlsx_report_no_tasks_project(self):
        """get_xlsx_report should complete without error for a project with no tasks."""
        empty_project = self.env['project.project'].create({
            'name': 'Empty Project',
            'user_id': self.admin_user.id,
        })
        wizard = self._wizard()
        response = self._run_xlsx(wizard, {'record': empty_project.id})
        response.stream.seek(0)
        self.assertGreater(len(response.stream.read()), 0)