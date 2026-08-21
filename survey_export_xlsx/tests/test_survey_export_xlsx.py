# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import io
from unittest.mock import MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestSurveyExportXlsx(TransactionCase):
    """Test suite for the survey_export_xlsx module.

    Covers:
    - Survey model: action_print_xlsx_report returns a correct wizard action.
    - Wizard: creation with survey_ids, partner_id constraints.
    - _onchange_partner_id: domain returned when completed inputs exist,
      ValidationError when no participants.
    - action_print_survey_xlsx_report: data grouped correctly with/without
      partner filter.
    - get_xlsx_report: XLSX bytes generated for non-empty and empty datasets.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Partner ──────────────────────────────────────────────────────────
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Respondent',
            'email': 'respondent@example.com',
        })

        # ── Survey ───────────────────────────────────────────────────────────
        cls.survey = cls.env['survey.survey'].create({
            'title': 'Customer Satisfaction Survey',
            'access_mode': 'public',
            'users_login_required': False,
        })

        # ── Question ─────────────────────────────────────────────────────────
        cls.question = cls.env['survey.question'].create({
            'title': 'How satisfied are you?',
            'survey_id': cls.survey.id,
            'question_type': 'text_box',
            'sequence': 10,
        })

        # ── User input (completed) ────────────────────────────────────────────
        cls.user_input = cls.env['survey.user_input'].create({
            'survey_id': cls.survey.id,
            'partner_id': cls.partner.id,
            'state': 'done',
        })

        # ── Input line ────────────────────────────────────────────────────────
        cls.input_line = cls.env['survey.user_input.line'].create({
            'survey_id': cls.survey.id,
            'user_input_id': cls.user_input.id,
            'question_id': cls.question.id,
            'value_char_box': 'Very satisfied',
        })

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Survey model – action_print_xlsx_report
    # ─────────────────────────────────────────────────────────────────────────

    def test_action_print_xlsx_report_returns_act_window(self):
        """action_print_xlsx_report should return an ir.actions.act_window."""
        action = self.survey.action_print_xlsx_report()
        self.assertEqual(action.get('type'), 'ir.actions.act_window',
                         "Action type must be 'ir.actions.act_window'.")

    def test_action_print_xlsx_report_target_new(self):
        """The wizard action must open in a 'new' dialog."""
        action = self.survey.action_print_xlsx_report()
        self.assertEqual(action.get('target'), 'new',
                         "The wizard must open as a new dialog.")

    def test_action_print_xlsx_report_res_model(self):
        """The action must point to the 'survey.xlsx.report' transient model."""
        action = self.survey.action_print_xlsx_report()
        self.assertEqual(action.get('res_model'), 'survey.xlsx.report',
                         "res_model should be 'survey.xlsx.report'.")

    def test_action_print_xlsx_report_context_survey_ids(self):
        """The action context must include default_survey_ids with the survey id."""
        action = self.survey.action_print_xlsx_report()
        context = action.get('context', {})
        self.assertIn(self.survey.id, context.get('default_survey_ids', []),
                      "context['default_survey_ids'] must include the survey id.")

    def test_action_print_xlsx_report_view_mode(self):
        """The action must open in 'form' view mode."""
        action = self.survey.action_print_xlsx_report()
        self.assertEqual(action.get('view_mode'), 'form',
                         "view_mode should be 'form'.")

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Wizard – basic creation
    # ─────────────────────────────────────────────────────────────────────────

    def test_wizard_creation_with_survey_ids(self):
        """The wizard can be created with survey_ids."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        self.assertIn(self.survey, wizard.survey_ids,
                      "Survey must be linked to the wizard after creation.")

    def test_wizard_creation_without_partner(self):
        """Wizard created without a partner should have no partner_id."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        self.assertFalse(wizard.partner_id,
                         "partner_id must be empty when not provided.")

    def test_wizard_creation_with_partner(self):
        """Wizard can be created with both survey_ids and partner_id."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
            'partner_id': self.partner.id,
        })
        self.assertEqual(wizard.partner_id, self.partner,
                         "partner_id must match the assigned partner.")

    def test_wizard_is_transient(self):
        """survey.xlsx.report must be a TransientModel."""
        model = self.env['survey.xlsx.report']
        self.assertTrue(model._transient,
                        "survey.xlsx.report must be a TransientModel.")

    # ─────────────────────────────────────────────────────────────────────────
    # 3. _onchange_partner_id – domain / ValidationError
    # ─────────────────────────────────────────────────────────────────────────

    def test_onchange_partner_id_returns_domain(self):
        """_onchange_partner_id returns a domain containing the partner."""
        wizard = self.env['survey.xlsx.report'].new({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard._onchange_partner_id()
        domain_ids = result['domain']['partner_id'][0][2]
        self.assertIn(self.partner.id, domain_ids,
                      "The respondent partner must appear in the returned domain.")

    def test_onchange_partner_id_no_participants_raises(self):
        """ValidationError raised when survey has no completed responses."""
        other_survey = self.env['survey.survey'].create({
            'title': 'Empty Survey',
            'access_mode': 'public',
        })
        wizard = self.env['survey.xlsx.report'].new({
            'survey_ids': [(4, other_survey.id)],
        })
        with self.assertRaises(ValidationError):
            wizard._onchange_partner_id()

    def test_onchange_partner_id_excludes_draft_inputs(self):
        """Only 'done' inputs are considered; draft inputs are excluded."""
        draft_partner = self.env['res.partner'].create({
            'name': 'Draft Partner',
        })
        draft_survey = self.env['survey.survey'].create({
            'title': 'Draft Survey',
            'access_mode': 'public',
        })
        self.env['survey.user_input'].create({
            'survey_id': draft_survey.id,
            'partner_id': draft_partner.id,
            'state': 'new',
        })
        wizard = self.env['survey.xlsx.report'].new({
            'survey_ids': [(4, draft_survey.id)],
        })
        with self.assertRaises(ValidationError):
            wizard._onchange_partner_id()

    # ─────────────────────────────────────────────────────────────────────────
    # 4. action_print_survey_xlsx_report – data compilation
    # ─────────────────────────────────────────────────────────────────────────

    def test_report_action_type(self):
        """action_print_survey_xlsx_report must return an ir.actions.report."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        self.assertEqual(result.get('type'), 'ir.actions.report',
                         "Returned type must be 'ir.actions.report'.")

    def test_report_type_xlsx(self):
        """report_type in the returned action must be 'xlsx'."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        self.assertEqual(result.get('report_type'), 'xlsx',
                         "report_type must be 'xlsx'.")

    def test_report_data_model(self):
        """The returned action data must reference survey.xlsx.report model."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        self.assertEqual(result['data']['model'], 'survey.xlsx.report',
                         "data model must be 'survey.xlsx.report'.")

    def test_report_data_output_format(self):
        """output_format in action data must be 'xlsx'."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        self.assertEqual(result['data']['output_format'], 'xlsx',
                         "output_format must be 'xlsx'.")

    def test_report_data_contains_records(self):
        """Compiled options JSON must include at least one 'record' entry."""
        import json as _json
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        options = _json.loads(result['data']['options'])
        self.assertTrue(len(options.get('record', [])) > 0,
                        "options['record'] must contain at least one survey entry.")

    def test_report_data_grouped_by_survey_name(self):
        """Each record entry must have the correct survey_name."""
        import json as _json
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        options = _json.loads(result['data']['options'])
        survey_names = [r['survey_name'] for r in options['record']]
        self.assertIn(self.survey.title, survey_names,
                      "The survey title must appear in grouped records.")

    def test_report_partner_filter(self):
        """When partner_id is set, options include the partner name."""
        import json as _json
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
            'partner_id': self.partner.id,
        })
        result = wizard.action_print_survey_xlsx_report()
        options = _json.loads(result['data']['options'])
        partner_names = [r.get('partner_id') for r in options['record']]
        self.assertIn(self.partner.name, partner_names,
                      "partner_id name must be present in records when filtered.")

    def test_report_no_partner_filter(self):
        """When no partner filter, partner_id in each record must be falsy."""
        import json as _json
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        options = _json.loads(result['data']['options'])
        for rec in options['record']:
            self.assertFalse(rec.get('partner_id'),
                             "Without a partner filter, partner_id should be falsy.")

    def test_report_data_per_record_keys(self):
        """Each answer entry inside 'data' must have required keys."""
        import json as _json
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        options = _json.loads(result['data']['options'])
        required_keys = {'survey_name', 'create_date', 'user_name',
                         'question', 'answer'}
        for group in options['record']:
            for entry in group['data']:
                self.assertTrue(required_keys.issubset(entry.keys()),
                                f"Answer entry missing keys: "
                                f"{required_keys - entry.keys()}")

    def test_report_empty_when_no_done_inputs(self):
        """Report options must have no records when no survey input is done."""
        import json as _json
        empty_survey = self.env['survey.survey'].create({
            'title': 'No Responses Survey',
            'access_mode': 'public',
        })
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, empty_survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        options = _json.loads(result['data']['options'])
        self.assertEqual(options.get('record', []), [],
                         "Options should have no records for a survey with "
                         "no completed inputs.")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. get_xlsx_report – binary output
    # ─────────────────────────────────────────────────────────────────────────

    def _make_response_mock(self):
        """Return a mock object that simulates a werkzeug response stream."""
        buf = io.BytesIO()
        response = MagicMock()
        response.stream = buf
        return response, buf

    def test_get_xlsx_report_produces_bytes(self):
        """get_xlsx_report must write non-empty bytes to the response stream."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        dict_data = {
            'record': [
                {
                    'survey_name': 'Test Survey',
                    'partner_id': None,
                    'data': [
                        {
                            'user_name': 'Alice',
                            'create_date': '2025-01-01 10:00:00',
                            'question': 'Rate us',
                            'answer': '5',
                        }
                    ],
                }
            ]
        }
        response, buf = self._make_response_mock()
        wizard.get_xlsx_report(dict_data, response)
        content = buf.getvalue()
        self.assertTrue(len(content) > 0,
                        "XLSX output must be non-empty bytes.")

    def test_get_xlsx_report_valid_xlsx_signature(self):
        """The bytes written must begin with the XLSX (ZIP) file signature."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        dict_data = {
            'record': [
                {
                    'survey_name': 'Sig Test Survey',
                    'partner_id': None,
                    'data': [
                        {
                            'user_name': 'Bob',
                            'create_date': '2025-06-01 09:00:00',
                            'question': 'Comment?',
                            'answer': 'Good',
                        }
                    ],
                }
            ]
        }
        response, buf = self._make_response_mock()
        wizard.get_xlsx_report(dict_data, response)
        content = buf.getvalue()
        # XLSX files are ZIP archives; they start with PK magic bytes
        self.assertTrue(content[:2] == b'PK',
                        "XLSX file must start with ZIP magic bytes 'PK'.")

    def test_get_xlsx_report_with_partner_filter(self):
        """get_xlsx_report renders partner-filtered layout without error."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
            'partner_id': self.partner.id,
        })
        dict_data = {
            'record': [
                {
                    'survey_name': 'Partner Survey',
                    'partner_id': 'Alice',
                    'data': [
                        {
                            'user_name': 'Alice',
                            'create_date': '2025-01-15 08:30:00',
                            'question': 'Happy?',
                            'answer': 'Yes',
                        }
                    ],
                }
            ]
        }
        response, buf = self._make_response_mock()
        wizard.get_xlsx_report(dict_data, response)
        self.assertTrue(len(buf.getvalue()) > 0,
                        "XLSX output must be produced for partner-filtered data.")

    def test_get_xlsx_report_empty_data(self):
        """get_xlsx_report with empty record list writes the 'No data' sheet."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        dict_data = {'record': []}
        response, buf = self._make_response_mock()
        wizard.get_xlsx_report(dict_data, response)
        content = buf.getvalue()
        self.assertTrue(len(content) > 0,
                        "XLSX output must be non-empty even for an empty dataset.")
        self.assertTrue(content[:2] == b'PK',
                        "Empty-data XLSX must still be a valid ZIP/XLSX file.")

    def test_get_xlsx_report_multiple_surveys(self):
        """get_xlsx_report handles multiple survey groups correctly."""
        second_survey = self.env['survey.survey'].create({
            'title': 'Product Feedback Survey',
            'access_mode': 'public',
        })
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id), (4, second_survey.id)],
        })
        dict_data = {
            'record': [
                {
                    'survey_name': 'Customer Satisfaction Survey',
                    'partner_id': None,
                    'data': [{'user_name': 'Alice',
                               'create_date': '2025-01-01',
                               'question': 'Q1', 'answer': 'A1'}],
                },
                {
                    'survey_name': 'Product Feedback Survey',
                    'partner_id': None,
                    'data': [{'user_name': 'Bob',
                               'create_date': '2025-02-01',
                               'question': 'Q2', 'answer': 'A2'}],
                },
            ]
        }
        response, buf = self._make_response_mock()
        wizard.get_xlsx_report(dict_data, response)
        content = buf.getvalue()
        self.assertTrue(content[:2] == b'PK',
                        "Multi-survey XLSX must be a valid ZIP/XLSX file.")

    # ─────────────────────────────────────────────────────────────────────────
    # 6. Edge cases
    # ─────────────────────────────────────────────────────────────────────────

    def test_action_print_xlsx_report_multiple_surveys(self):
        """action_print_xlsx_report with multiple surveys includes all ids."""
        survey2 = self.env['survey.survey'].create({
            'title': 'Secondary Survey',
            'access_mode': 'public',
        })
        surveys = self.survey | survey2
        action = surveys.action_print_xlsx_report()
        context_ids = action['context']['default_survey_ids']
        self.assertIn(self.survey.id, context_ids)
        self.assertIn(survey2.id, context_ids)

    def test_report_name_in_action(self):
        """Report name in the action data must be set."""
        wizard = self.env['survey.xlsx.report'].create({
            'survey_ids': [(4, self.survey.id)],
        })
        result = wizard.action_print_survey_xlsx_report()
        self.assertTrue(result['data'].get('report_name'),
                        "report_name must be set in action data.")

    def test_wizard_survey_ids_readonly(self):
        """survey_ids field metadata must mark the field as readonly."""
        field_def = self.env['survey.xlsx.report']._fields.get('survey_ids')
        self.assertIsNotNone(field_def, "survey_ids field must exist on the model.")
        self.assertTrue(field_def.readonly,
                        "survey_ids must be declared as readonly.")
