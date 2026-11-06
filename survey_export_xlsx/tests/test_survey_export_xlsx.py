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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import io
import json
import urllib.parse
import zipfile
from unittest.mock import MagicMock, patch

from werkzeug.wrappers import Response

from odoo.addons.survey_export_xlsx.controllers import survey_export_xlsx
from odoo.addons.survey_export_xlsx.controllers.survey_export_xlsx import SurveyXlsReportController
from odoo.tests import common, tagged


class MockStreamResponse:
    """Mock HTTP response object to capture stream writes in get_xlsx_report."""
    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestSurveyExportXlsx(common.TransactionCase):
    """Test suite for survey_export_xlsx module models and wizards."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test partners
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test Respondent One',
            'email': 'respondent1@example.com',
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Test Respondent Two',
            'email': 'respondent2@example.com',
        })

        # Create two test surveys
        cls.survey_1 = cls.env['survey.survey'].create({
            'title': 'Customer Feedback Survey 2026',
        })
        cls.survey_2 = cls.env['survey.survey'].create({
            'title': 'Product Satisfaction Survey 2026',
        })
        cls.empty_survey = cls.env['survey.survey'].create({
            'title': 'Empty Survey Without Answers',
        })

        # Create survey questions for survey_1
        cls.question_1 = cls.env['survey.question'].create({
            'survey_id': cls.survey_1.id,
            'title': 'Overall satisfaction level?',
            'question_type': 'char_box',
        })
        cls.question_2 = cls.env['survey.question'].create({
            'survey_id': cls.survey_1.id,
            'title': 'Any additional comments?',
            'question_type': 'char_box',
        })

        # Create survey question for survey_2
        cls.question_survey_2 = cls.env['survey.question'].create({
            'survey_id': cls.survey_2.id,
            'title': 'Would you recommend us?',
            'question_type': 'char_box',
        })

        # Create user inputs (answers) for survey_1 with state 'done'
        cls.user_input_1 = cls.env['survey.user_input'].create({
            'survey_id': cls.survey_1.id,
            'partner_id': cls.partner_1.id,
            'state': 'done',
        })
        cls.line_1_q1 = cls.env['survey.user_input.line'].create({
            'user_input_id': cls.user_input_1.id,
            'survey_id': cls.survey_1.id,
            'question_id': cls.question_1.id,
            'value_char_box': 'Very High',
            'answer_type': 'char_box',
        })
        cls.line_1_q2 = cls.env['survey.user_input.line'].create({
            'user_input_id': cls.user_input_1.id,
            'survey_id': cls.survey_1.id,
            'question_id': cls.question_2.id,
            'value_char_box': 'Keep up the great work!',
            'answer_type': 'char_box',
        })

        cls.user_input_2 = cls.env['survey.user_input'].create({
            'survey_id': cls.survey_1.id,
            'partner_id': cls.partner_2.id,
            'state': 'done',
        })
        cls.line_2_q1 = cls.env['survey.user_input.line'].create({
            'user_input_id': cls.user_input_2.id,
            'survey_id': cls.survey_1.id,
            'question_id': cls.question_1.id,
            'value_char_box': 'Moderate',
            'answer_type': 'char_box',
        })

        # Create an incomplete user input (state 'new') for survey_2 (should be excluded)
        cls.user_input_incomplete = cls.env['survey.user_input'].create({
            'survey_id': cls.survey_2.id,
            'partner_id': cls.partner_1.id,
            'state': 'new',
        })

        # Create a standard internal test user with Survey user permissions
        group_user = cls.env.ref('base.group_user')
        group_survey_user = cls.env.ref('survey.group_survey_user')
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Survey Test User',
            'login': 'survey_test_user',
            'email': 'survey_user@example.com',
            'group_ids': [(6, 0, [group_user.id, group_survey_user.id])],
        })

    def test_01_server_action_and_views(self):
        """Verify the server action and the wizard view exist and are valid."""
        server_action = self.env.ref('survey_export_xlsx.survey_survey_action')
        self.assertTrue(server_action, "Server action survey_survey_action must exist.")
        self.assertEqual(server_action.state, 'code')
        self.assertEqual(server_action.model_id.model, 'survey.survey')

        # Test running server action with active_model context
        action_res = server_action.with_context(
            active_ids=[self.survey_1.id],
            active_id=self.survey_1.id,
            active_model='survey.survey',
        ).run()
        self.assertEqual(action_res.get('res_model'), 'survey.xlsx.report')

        # Verify wizard form view loads without XML errors
        view = self.env.ref('survey_export_xlsx.survey_xlsx_report_view_form')
        self.assertTrue(view, "Wizard form view survey_xlsx_report_view_form must exist.")
        views = self.env['survey.xlsx.report'].get_views([(view.id, 'form')])
        self.assertIn('form', views.get('views', {}))

    def test_02_survey_action_print_xlsx_report(self):
        """Verify action_print_xlsx_report on single and multiple survey records."""
        # Single record
        action_single = self.survey_1.action_print_xlsx_report()
        self.assertEqual(action_single.get('name'), 'Survey Answer XLSX Report')
        self.assertEqual(action_single.get('res_model'), 'survey.xlsx.report')
        self.assertEqual(action_single.get('view_mode'), 'form')
        self.assertEqual(action_single.get('type'), 'ir.actions.act_window')
        self.assertEqual(action_single.get('target'), 'new')
        self.assertEqual(action_single.get('context'), {'default_survey_ids': [self.survey_1.id]})

        # Multiple records
        surveys = self.survey_1 + self.survey_2
        action_multi = surveys.action_print_xlsx_report()
        self.assertEqual(action_multi.get('context'), {'default_survey_ids': surveys.ids})

    def test_03_wizard_partner_ids_computation(self):
        """Verify partner_ids computes partners who completed the surveys."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey_1.id])],
        })
        self.assertIn(self.partner_1, wizard.partner_ids)
        self.assertIn(self.partner_2, wizard.partner_ids)

    def test_04_wizard_empty_survey_no_partners(self):
        """Verify partner_ids is empty when no partners have completed the survey or no surveys selected."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.empty_survey.id])],
        })
        self.assertFalse(wizard.partner_ids)

        wizard_no_surveys = self.env['survey.xlsx.report'].create({})
        self.assertFalse(wizard_no_surveys.partner_ids)

    def test_05_action_print_survey_xlsx_report_all_partners(self):
        """Verify action_print_survey_xlsx_report compiles all completed survey answers."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey_1.id])],
        })
        action = wizard.action_print_survey_xlsx_report()

        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')
        data = action.get('data', {})
        self.assertEqual(data.get('model'), 'survey.xlsx.report')
        self.assertEqual(data.get('output_format'), 'xlsx')
        self.assertEqual(data.get('report_name'), 'Survey Question Answer Report')

        # Parse options JSON
        options = json.loads(data.get('options', '{}'))
        records = options.get('record', [])
        self.assertEqual(len(records), 1)
        survey_record = records[0]
        self.assertEqual(survey_record.get('survey_name'), self.survey_1.title)
        self.assertFalse(survey_record.get('partner_id'))

        answer_data = survey_record.get('data', [])
        # We expect 3 answers: 2 from partner_1 and 1 from partner_2
        self.assertEqual(len(answer_data), 3)
        user_names = [a.get('user_name') for a in answer_data]
        self.assertIn(self.partner_1.name, user_names)
        self.assertIn(self.partner_2.name, user_names)

    def test_06_action_print_survey_xlsx_report_filtered_by_partner(self):
        """Verify action_print_survey_xlsx_report filters answers when partner_id is selected."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey_1.id])],
            'partner_id': self.partner_1.id,
        })
        action = wizard.action_print_survey_xlsx_report()
        data = action.get('data', {})
        options = json.loads(data.get('options', '{}'))
        records = options.get('record', [])
        self.assertEqual(len(records), 1)

        survey_record = records[0]
        self.assertEqual(survey_record.get('partner_id'), self.partner_1.name)
        answer_data = survey_record.get('data', [])
        self.assertEqual(len(answer_data), 2)
        for ans in answer_data:
            self.assertEqual(ans.get('user_name'), self.partner_1.name)

    def test_07_action_print_survey_xlsx_report_multiple_surveys(self):
        """Verify report action handles multiple surveys."""
        # Add a done user input for survey_2
        user_input_survey_2 = self.env['survey.user_input'].create({
            'survey_id': self.survey_2.id,
            'partner_id': self.partner_1.id,
            'state': 'done',
        })
        self.env['survey.user_input.line'].create({
            'user_input_id': user_input_survey_2.id,
            'survey_id': self.survey_2.id,
            'question_id': self.question_survey_2.id,
            'value_char_box': 'Yes, absolutely!',
            'answer_type': 'char_box',
        })

        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey_1.id, self.survey_2.id])],
        })
        action = wizard.action_print_survey_xlsx_report()
        options = json.loads(action['data']['options'])
        records = options.get('record', [])
        survey_names = [r.get('survey_name') for r in records]
        self.assertIn(self.survey_1.title, survey_names)
        self.assertIn(self.survey_2.title, survey_names)

    def test_08_get_xlsx_report_with_partner(self):
        """Verify get_xlsx_report generates a valid Excel spreadsheet for partner-specific report."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey_1.id])],
            'partner_id': self.partner_1.id,
        })
        action = wizard.action_print_survey_xlsx_report()
        options = json.loads(action['data']['options'])

        mock_resp = MockStreamResponse()
        wizard.get_xlsx_report(options, mock_resp)
        xlsx_bytes = mock_resp.stream.getvalue()

        # Check valid non-empty content
        self.assertGreater(len(xlsx_bytes), 0)
        # XLSX files are ZIP packages starting with b'PK\x03\x04'
        self.assertTrue(xlsx_bytes.startswith(b'PK\x03\x04'))
        # Validate it can be parsed as a valid zip archive
        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
            self.assertIn('xl/workbook.xml', zf.namelist())
            self.assertIn('xl/worksheets/sheet1.xml', zf.namelist())

    def test_09_get_xlsx_report_without_partner(self):
        """Verify get_xlsx_report generates a valid Excel spreadsheet with multiple respondents."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey_1.id])],
        })
        action = wizard.action_print_survey_xlsx_report()
        options = json.loads(action['data']['options'])

        mock_resp = MockStreamResponse()
        wizard.get_xlsx_report(options, mock_resp)
        xlsx_bytes = mock_resp.stream.getvalue()

        self.assertGreater(len(xlsx_bytes), 0)
        self.assertTrue(xlsx_bytes.startswith(b'PK\x03\x04'))
        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
            self.assertIn('xl/workbook.xml', zf.namelist())

    def test_10_get_xlsx_report_empty_data(self):
        """Verify get_xlsx_report generates a valid Excel file even when no records exist."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.empty_survey.id])],
        })
        action = wizard.action_print_survey_xlsx_report()
        options = json.loads(action['data']['options'])

        mock_resp = MockStreamResponse()
        wizard.get_xlsx_report(options, mock_resp)
        xlsx_bytes = mock_resp.stream.getvalue()

        self.assertGreater(len(xlsx_bytes), 0)
        self.assertTrue(xlsx_bytes.startswith(b'PK\x03\x04'))
        with zipfile.ZipFile(io.BytesIO(xlsx_bytes)) as zf:
            self.assertIn('xl/workbook.xml', zf.namelist())

    def test_11_anonymous_respondent(self):
        """Verify report works when user_input has no partner (anonymous survey)."""
        anon_user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey_1.id,
            'partner_id': False,
            'state': 'done',
        })
        self.env['survey.user_input.line'].create({
            'user_input_id': anon_user_input.id,
            'survey_id': self.survey_1.id,
            'question_id': self.question_1.id,
            'value_char_box': 'Anonymous Response',
            'answer_type': 'char_box',
        })

        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey_1.id])],
        })
        action = wizard.action_print_survey_xlsx_report()
        options = json.loads(action['data']['options'])

        mock_resp = MockStreamResponse()
        wizard.get_xlsx_report(options, mock_resp)
        xlsx_bytes = mock_resp.stream.getvalue()
        self.assertTrue(xlsx_bytes.startswith(b'PK\x03\x04'))

    def test_12_security_access(self):
        """Verify a standard survey user has permissions on the wizard."""
        wizard_user = self.env['survey.xlsx.report'].with_user(self.internal_user).create({
            'survey_ids': [(6, 0, [self.survey_1.id])],
        })
        self.assertTrue(wizard_user.id)
        action = wizard_user.action_print_survey_xlsx_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')


@tagged('post_install', '-at_install')
class TestSurveyExportXlsxController(common.TransactionCase):
    """Test suite for /xlsx_reports controller route."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = SurveyXlsReportController()
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Controller Test Survey',
        })
        group_user = cls.env.ref('base.group_user')
        group_survey_user = cls.env.ref('survey.group_survey_user')
        cls.http_user = cls.env['res.users'].create({
            'name': 'HTTP Test User',
            'login': 'http_test_user',
            'email': 'httptest@example.com',
            'group_ids': [(6, 0, [group_user.id, group_survey_user.id])],
        })

    def test_13_controller_xlsx_report_download(self):
        """Verify /xlsx_reports endpoint returns valid Excel attachment for authenticated user."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(6, 0, [self.survey.id])],
        })
        action = wizard.action_print_survey_xlsx_report()
        data = action['data']

        mock_req = MagicMock()
        mock_req.session.uid = self.http_user.id
        mock_req.env = self.env
        mock_resp = Response()
        mock_resp.stream = io.BytesIO()
        mock_resp.set_cookie = MagicMock()
        mock_req.make_response = MagicMock(return_value=mock_resp)

        with patch.object(survey_export_xlsx, 'request', mock_req):
            self.controller.get_report_xlsx(
                model=data['model'],
                options=data['options'],
                output_format=data['output_format'],
                report_name=data['report_name'],
            )
            val = mock_resp.stream.getvalue()
            self.assertTrue(val.startswith(b'PK\x03\x04'), "Returned content must be valid XLSX zip archive")
            mock_resp.set_cookie.assert_called_with('fileToken', 'dummy-because-api-expects-one')

    def test_14_controller_xlsx_report_error_handling(self):
        """Verify /xlsx_reports endpoint returns error JSON when report generation raises an exception."""
        mock_req = MagicMock()
        mock_req.session.uid = self.http_user.id
        mock_req.env = self.env
        mock_req.make_response = lambda body, *a, **kw: Response(body)

        with patch.object(survey_export_xlsx, 'request', mock_req):
            resp = self.controller.get_report_xlsx(
                model='survey.xlsx.report',
                options=json.dumps({'record': 'invalid_string_not_iterable_list'}),
                output_format='xlsx',
                report_name='Error Test',
            )
            text = resp.get_data(as_text=True)
            self.assertIn('Odoo Server Error', text)

    def test_15_controller_xlsx_report_invalid_model(self):
        """Verify /xlsx_reports endpoint rejects unauthorized models."""
        mock_req = MagicMock()
        mock_req.session.uid = self.http_user.id
        mock_req.make_response = lambda body, *a, **kw: Response(body)

        with patch.object(survey_export_xlsx, 'request', mock_req):
            resp = self.controller.get_report_xlsx(
                model='res.users',
                options=json.dumps({'record': []}),
                output_format='xlsx',
                report_name='Unauthorized Model Test',
            )
            text = resp.get_data(as_text=True)
            self.assertIn('Invalid model', text)
