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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.http import Response
from odoo.tests import TransactionCase, tagged

from odoo.addons.enhanced_survey_management.controllers.enhanced_survey_management import (
    SurveyAnswerPortal,
    SurveyLoadContent,
    SurveyPortalView,
)
from odoo.addons.enhanced_survey_management.controllers.website_visibility import (
    WebsiteView,
)
from odoo.addons.enhanced_survey_management.controllers.xlsx_main import (
    XlsxReportController,
)


@tagged('post_install', '-at_install')
class TestEnhancedSurvey(TransactionCase):
    """Test suite for Enhanced Survey Management models and controllers."""

    @classmethod
    def setUpClass(cls):
        """Set up shared survey, partner, and portal user fixtures."""
        super().setUpClass()

        partner_fields = cls.env['res.partner']._fields
        if 'autopost_bills' in partner_fields:
            cls.env['ir.default'].set('res.partner', 'autopost_bills', 'never')
        if 'group_rfq' in partner_fields:
            cls.env['ir.default'].set('res.partner', 'group_rfq', 'default')
        if 'group_on' in partner_fields:
            cls.env['ir.default'].set('res.partner', 'group_on', 'default')

        cls.survey = cls.env['survey.survey'].create({
            'title': 'Enhanced Test Survey',
            'access_mode': 'public',
            'visibility': True,
        })

        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Participant',
            'email': 'participant@example.com',
        })

        portal_group = cls.env.ref('base.group_portal')
        cls.portal_user = cls.env['res.users'].create({
            'name': 'Test Portal User',
            'login': 'portal_user_test',
            'email': 'participant@example.com',
            'partner_id': cls.partner.id,
            'group_ids': [(6, 0, [portal_group.id])],
        })

    def test_01_question_barcode_validation(self):
        """Test barcode constraint validations on survey.question."""
        msg_short = "Should raise error if barcode length < 12"
        with self.assertRaises(ValidationError, msg=msg_short):
            self.env['survey.question'].create({
                'title': 'Test Barcode Short',
                'survey_id': self.survey.id,
                'question_type': 'barcode',
                'barcode': '123456789',
            })

        msg_long = "Should raise error if barcode length > 12"
        with self.assertRaises(ValidationError, msg=msg_long):
            self.env['survey.question'].create({
                'title': 'Test Barcode Long',
                'survey_id': self.survey.id,
                'question_type': 'barcode',
                'barcode': '1234567890123',
            })

        msg_letters = "Should raise error if barcode contains letters"
        with self.assertRaises(ValidationError, msg=msg_letters):
            self.env['survey.question'].create({
                'title': 'Test Barcode NonDigit',
                'survey_id': self.survey.id,
                'question_type': 'barcode',
                'barcode': '12345678901a',
            })

        question = self.env['survey.question'].create({
            'title': 'Test Barcode Valid',
            'survey_id': self.survey.id,
            'question_type': 'barcode',
            'barcode': '123456789012',
        })
        self.assertEqual(question.barcode, '123456789012')
        question._onchange_barcode()

    def test_02_get_selection_values(self):
        """Test fetching selection values for choice list questions."""
        question = self.env['survey.question'].create({
            'title': 'Select your preferred color',
            'survey_id': self.survey.id,
            'question_type': 'selection',
            'selection_ids': [
                (0, 0, {'name': 'Red'}),
                (0, 0, {'name': 'Blue'}),
                (0, 0, {'name': 'Green'}),
            ],
        })
        selections = question.get_selection_values()
        self.assertEqual(len(selections), 3)
        self.assertEqual(
            selections.mapped('name'),
            ['Red', 'Blue', 'Green'],
        )

    def test_03_prepare_model_id(self):
        """Test model list helper (prepare_model_id) for many2one fields."""
        model_partner = self.env['ir.model'].search(
            [('model', '=', 'res.partner')],
            limit=1,
        )
        question = self.env['survey.question'].create({
            'title': 'Choose a partner',
            'survey_id': self.survey.id,
            'question_type': 'many2one',
            'model_id': model_partner.id,
        })
        options = question.prepare_model_id(model_partner)
        self.assertTrue(len(options) > 0, "Should load existing partners")
        self.assertIn('name', options[0])

        options_fallback = question.prepare_model_id(None)
        self.assertEqual(len(options_fallback), len(options))

        q_empty = self.env['survey.question'].create({
            'title': 'No model question',
            'survey_id': self.survey.id,
            'question_type': 'many2one',
        })
        self.assertEqual(q_empty.prepare_model_id(None), [])

    def test_04_save_custom_answers(self):
        """Test saving different custom answer types in user inputs."""
        q_time = self.env['survey.question'].create({
            'title': 'Time Question',
            'survey_id': self.survey.id,
            'question_type': 'time',
        })
        q_url = self.env['survey.question'].create({
            'title': 'URL Question',
            'survey_id': self.survey.id,
            'question_type': 'url',
        })
        q_email = self.env['survey.question'].create({
            'title': 'Email Question',
            'survey_id': self.survey.id,
            'question_type': 'email',
        })
        q_pass = self.env['survey.question'].create({
            'title': 'Password Question',
            'survey_id': self.survey.id,
            'question_type': 'password',
        })
        q_range = self.env['survey.question'].create({
            'title': 'Range Question',
            'survey_id': self.survey.id,
            'question_type': 'range',
        })
        q_week = self.env['survey.question'].create({
            'title': 'Week Question',
            'survey_id': self.survey.id,
            'question_type': 'week',
        })
        q_color = self.env['survey.question'].create({
            'title': 'Color Question',
            'survey_id': self.survey.id,
            'question_type': 'color',
        })
        q_month = self.env['survey.question'].create({
            'title': 'Month Question',
            'survey_id': self.survey.id,
            'question_type': 'month',
        })
        q_sel = self.env['survey.question'].create({
            'title': 'Selection Question',
            'survey_id': self.survey.id,
            'question_type': 'selection',
        })
        q_m2o = self.env['survey.question'].create({
            'title': 'Many2one Question',
            'survey_id': self.survey.id,
            'question_type': 'many2one',
        })
        q_m2m = self.env['survey.question'].create({
            'title': 'Many2many Question',
            'survey_id': self.survey.id,
            'question_type': 'many2many',
        })
        q_address = self.env['survey.question'].create({
            'title': 'Address Question',
            'survey_id': self.survey.id,
            'question_type': 'address',
        })
        q_name = self.env['survey.question'].create({
            'title': 'Name Question',
            'survey_id': self.survey.id,
            'question_type': 'name',
        })
        q_file = self.env['survey.question'].create({
            'title': 'File Question',
            'survey_id': self.survey.id,
            'question_type': 'file',
        })

        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner.id,
        })

        user_input._save_lines(q_time, "14:30")
        user_input._save_lines(q_url, "https://example.com")
        user_input._save_lines(q_email, "test@example.com")
        user_input._save_lines(q_pass, "secret123")
        user_input._save_lines(q_range, "10-20")
        user_input._save_lines(q_week, "2025-W20")
        user_input._save_lines(q_color, "#FF0000")
        user_input._save_lines(q_month, "2025-05")
        user_input._save_lines(q_sel, "Option A")
        user_input._save_lines(
            q_m2o,
            [str(self.partner.id), self.partner.name],
        )
        user_input._save_lines(q_m2m, "Tag A, Tag B")
        user_input._save_lines(
            q_address,
            {f"{q_address.id}-street": "Main Street"},
        )
        user_input._save_lines(q_name, {f"{q_name.id}-first": "John"})
        encoded_data = base64.b64encode(b"dummy_data").decode("utf-8")
        user_input._save_lines(q_file, [encoded_data, "test.txt"])

        user_input._save_lines(q_email, "updated@example.com")
        user_input._save_lines(q_color, "   ")

        line_sel_helper = user_input._save_line_selection_answer(
            q_sel,
            "Option B",
        )
        self.assertEqual(line_sel_helper.value_selection, "Option B")

        lines = user_input.user_input_line_ids

        line_time = lines.filtered(lambda line: line.question_id == q_time)
        self.assertEqual(line_time.value_time, 14.30)
        self.assertEqual(line_time.get_value_time(), "14:30")

        line_url = lines.filtered(lambda line: line.question_id == q_url)
        self.assertEqual(line_url.value_url, "https://example.com")

        line_email = lines.filtered(lambda line: line.question_id == q_email)
        self.assertEqual(line_email.value_email, "updated@example.com")

        line_pass = lines.filtered(lambda line: line.question_id == q_pass)
        self.assertEqual(line_pass.value_password, "secret123")

        line_range = lines.filtered(lambda line: line.question_id == q_range)
        self.assertEqual(line_range.value_range, "10-20")

        line_week = lines.filtered(lambda line: line.question_id == q_week)
        self.assertEqual(line_week.value_week, "2025-W20")

        line_color = lines.filtered(lambda line: line.question_id == q_color)
        self.assertTrue(line_color.skipped)

        line_month = lines.filtered(lambda line: line.question_id == q_month)
        self.assertEqual(line_month.value_month, "2025-05")

        line_sel = lines.filtered(lambda line: line.question_id == q_sel)
        self.assertTrue(len(line_sel) >= 1)

        line_m2o = lines.filtered(lambda line: line.question_id == q_m2o)
        self.assertEqual(line_m2o.value_many2one, str(self.partner.id))
        self.assertEqual(line_m2o.value_many2one_option, self.partner.name)

        line_m2m = lines.filtered(lambda line: line.question_id == q_m2m)
        self.assertEqual(line_m2m.value_many2many, "Tag A, Tag B")

        line_address = lines.filtered(lambda line: line.question_id == q_address)
        self.assertEqual(
            line_address.get_value_address("street"),
            "Main Street",
        )
        self.assertEqual(line_address.get_value_address("city"), "")

        line_name = lines.filtered(lambda line: line.question_id == q_name)
        self.assertEqual(line_name.get_value_name("first"), "John")
        self.assertEqual(line_name.get_value_name("last"), "")

        line_file = lines.filtered(lambda line: line.question_id == q_file)
        self.assertEqual(line_file.filename, "test.txt")
        file_bytes = bytes(line_file.file_data) if line_file.file_data else b""
        self.assertEqual(file_bytes, b"dummy_data")

    def test_05_display_name_and_value_getters(self):
        """Test _compute_display_name and helper getters for all types."""
        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
        })
        q_gen = self.env['survey.question'].create({
            'title': 'General',
            'survey_id': self.survey.id,
        })

        test_cases = [
            ('char_box', {'value_char_box': 'Short Text'}, 'Short Text'),
            (
                'text_box',
                {'value_text_box': 'Long Description' * 10},
                'Long Description' * 10,
            ),
            ('numerical_box', {'value_numerical_box': 42.5}, '42.5'),
            (
                'date',
                {'value_date': fields.Date.from_string('2025-05-15')},
                '2025-05-15',
            ),
            (
                'datetime',
                {
                    'value_datetime': fields.Datetime.from_string(
                        '2025-05-15 10:30:00',
                    ),
                },
                '2025-05-15 10:30:00',
            ),
            ('time', {'value_time': 15.45}, '15.45'),
            ('month', {'value_month': '2025-06'}, '2025-06'),
            (
                'address',
                {'value_address': '{"street": "Baker St"}'},
                '{"street": "Baker St"}',
            ),
            (
                'name',
                {'value_name': '{"first": "Sherlock"}'},
                '{"first": "Sherlock"}',
            ),
            ('url', {'value_url': 'https://odoo.com'}, 'https://odoo.com'),
            (
                'many2one',
                {'value_many2one': '1', 'value_many2one_option': 'Partner X'},
                'Partner X',
            ),
            ('many2many', {'value_many2many': 'Tag 1, Tag 2'}, 'Tag 1, Tag 2'),
            ('week', {'value_week': '2025-W22'}, '2025-W22'),
            ('email', {'value_email': 'info@test.com'}, 'info@test.com'),
            ('range', {'value_range': '5-15'}, '5-15'),
            (
                'matrix',
                {'value_matrix': '{"col1": "val1"}'},
                '{"col1": "val1"}',
            ),
            ('password', {'value_password': 'mypassword'}, 'mypassword'),
            ('color', {'value_color': '#00FF00'}, '#00FF00'),
            (
                'selection',
                {'value_selection': 'Selected Option'},
                'Selected Option',
            ),
            ('barcode', {'value_barcode': '123456789012'}, '123456789012'),
            ('qr', {'value_qr': 'QR_CODE_DATA'}, 'QR_CODE_DATA'),
            (
                'file',
                {
                    'value_file': self.env['ir.attachment'].create({
                        'name': 'document.pdf',
                        'raw': b'test',
                    }).id,
                    'filename': 'document.pdf',
                },
                'document.pdf',
            ),
        ]

        for ans_type, vals, expected_prefix in test_cases:
            line_vals = {
                'user_input_id': user_input.id,
                'question_id': q_gen.id,
                'answer_type': ans_type,
            }
            line_vals.update(vals)
            line = self.env['survey.user_input.line'].create(line_vals)
            line._compute_display_name()
            self.assertTrue(
                str(line.display_name).startswith(str(expected_prefix)[:15]),
                f"Failed for {ans_type}: {line.display_name}",
            )

        line_skipped = self.env['survey.user_input.line'].create({
            'user_input_id': user_input.id,
            'question_id': q_gen.id,
            'answer_type': False,
            'skipped': True,
        })
        line_skipped._compute_display_name()
        self.assertEqual(line_skipped.display_name, 'Skipped')

        line_empty = self.env['survey.user_input.line'].create({
            'user_input_id': user_input.id,
            'question_id': q_gen.id,
        })
        self.assertIsNone(line_empty.get_value_time())
        self.assertEqual(line_empty.get_value_address('field'), '')
        self.assertIsNone(line_empty.get_value_matrix('col'))
        self.assertEqual(line_empty.get_value_name('field'), '')

        line_invalid_json = self.env['survey.user_input.line'].create({
            'user_input_id': user_input.id,
            'question_id': q_gen.id,
            'value_address': '{invalid_json',
            'value_matrix': '{invalid_json',
            'value_name': '{invalid_json',
        })
        self.assertEqual(line_invalid_json.get_value_address('field'), '')
        self.assertIsNone(line_invalid_json.get_value_matrix('col'))
        self.assertEqual(line_invalid_json.get_value_name('field'), '')

    def test_06_custom_matrix_save(self):
        """Test custom matrix saving path and get_value_matrix."""
        q_matrix = self.env['survey.question'].create({
            'title': 'Custom Matrix Question',
            'survey_id': self.survey.id,
            'question_type': 'matrix',
            'matrix_subtype': 'custom',
        })

        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner.id,
        })

        matrix_answers = {f"col1-{q_matrix.id}": "Matrix Answer 1"}
        old_answers = self.env['survey.user_input.line'].search([
            ('user_input_id', '=', user_input.id),
            ('question_id', '=', q_matrix.id),
        ])

        line = user_input._save_line_matrix(
            q_matrix,
            old_answers,
            matrix_answers,
        )
        self.assertTrue(line)
        self.assertEqual(line.answer_type, 'matrix')
        self.assertEqual(line.get_value_matrix('col1'), 'Matrix Answer 1')

    def test_07_qr_and_barcode_answers(self):
        """Test saving QR and barcode answers."""
        q_qr = self.env['survey.question'].create({
            'title': 'QR Question',
            'survey_id': self.survey.id,
            'question_type': 'qr',
        })
        q_barcode = self.env['survey.question'].create({
            'title': 'Barcode Question',
            'survey_id': self.survey.id,
            'question_type': 'barcode',
            'barcode': '123456789012',
        })

        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner.id,
        })

        user_input._save_lines(q_qr, "QR_PAYLOAD_123")
        user_input._save_lines(q_barcode, "123456789012")

        lines = user_input.user_input_line_ids
        line_qr = lines.filtered(lambda line: line.question_id == q_qr)
        self.assertEqual(line_qr.value_qr, "QR_PAYLOAD_123")
        line_qr._compute_display_name()
        self.assertEqual(line_qr.display_name, "QR_PAYLOAD_123")

        line_barcode = lines.filtered(lambda line: line.question_id == q_barcode)
        self.assertEqual(line_barcode.value_barcode, "123456789012")
        line_barcode._compute_display_name()
        self.assertEqual(line_barcode.display_name, "123456789012")

    def test_08_portal_controller(self):
        """Test portal controller methods for participant survey access."""
        self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner.id,
            'state': 'done',
        })

        portal = SurveyAnswerPortal()
        mock_req = MagicMock()
        mock_req.env = self.env(user=self.portal_user)
        mock_req.uid = self.portal_user.id
        patch_target = (
            'odoo.addons.enhanced_survey_management.controllers'
            '.enhanced_survey_management.request'
        )
        with patch(patch_target, new=mock_req):
            model_name, domain, access = portal._prepare_portal_counter_values(
                'survey_count',
            )
            self.assertEqual(model_name, 'survey.user_input')
            self.assertEqual(access, 'sudo')
            self.assertEqual(
                self.env[model_name].sudo().search_count(domain),
                1,
            )

            portal_view = SurveyPortalView()
            mock_req.render = MagicMock(return_value="portal_rendered")
            res = portal_view.portal_my_survey()
            self.assertEqual(res.status_code, 200)
            self.assertIn("portal_rendered", res.get_data(as_text=True))
            mock_req.render.assert_called_once()
            args, _ = mock_req.render.call_args
            self.assertEqual(
                args[0],
                "enhanced_survey_management.portal_survey_result",
            )
            self.assertEqual(len(args[1]['survey_list']), 1)

            mock_req.render.reset_mock()
            res_view = portal_view.survey_view(self.survey.id)
            self.assertEqual(res_view.status_code, 200)
            self.assertIn("portal_rendered", res_view.get_data(as_text=True))
            mock_req.render.assert_called_once()
            args, _ = mock_req.render.call_args
            self.assertEqual(
                args[0],
                "enhanced_survey_management.portal_survey_result_view",
            )
            self.assertEqual(args[1]['survey'], self.survey.title)

            load_controller = SurveyLoadContent()
            country = self.env['res.country'].search([], limit=1)
            state = self.env['res.country.state'].search(
                [('country_id', '=', country.id)],
                limit=1,
            )
            if not state:
                state = self.env['res.country.state'].create({
                    'name': 'Teststate',
                    'code': 'TS99',
                    'country_id': country.id,
                })
            res_country = load_controller.load_country()
            self.assertIn(country.name, res_country['name'])

            res_state = load_controller.load_states(country_id=country.name)
            self.assertIn(state.name, res_state['name'])

    def test_09_xlsx_export(self):
        """Test XLSX report generation controller and model action."""
        action = self.survey.action_answer_report_download()
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertEqual(action.get('url'), f'/xlsx_report/{self.survey.id}')

        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner.id,
        })
        q_time = self.env['survey.question'].create({
            'title': 'Time Question',
            'survey_id': self.survey.id,
            'question_type': 'time',
        })
        user_input._save_lines(q_time, "14:30")

        controller = XlsxReportController()
        mock_req = MagicMock()
        mock_req.env = self.env

        def fake_make_response(data, headers=None):
            """Wrap raw response stream into Werkzeug Response."""
            return Response(data, headers=headers)

        mock_req.make_response = fake_make_response

        patch_target = (
            'odoo.addons.enhanced_survey_management.controllers'
            '.xlsx_main.request'
        )
        with patch(patch_target, new=mock_req):
            res = controller.get_report_xlsx(survey_id=self.survey)
            self.assertEqual(res.status_code, 200)
            xlsx_content = res.get_data()
            self.assertTrue(
                len(xlsx_content) > 0,
                "XLSX file stream should not be empty",
            )
            self.assertTrue(
                xlsx_content.startswith(b'PK'),
                "XLSX file should start with PK zip header",
            )

    def test_10_website_visibility(self):
        """Test website public survey listing."""
        self.survey.access_mode = 'website'
        controller = WebsiteView()
        mock_req = MagicMock()
        mock_req.env = self.env
        mock_req.render = MagicMock(return_value="website_rendered")

        patch_target = (
            'odoo.addons.enhanced_survey_management.controllers'
            '.website_visibility.request'
        )
        with patch(patch_target, new=mock_req):
            res = controller.public_user_access()
            self.assertEqual(res.status_code, 200)
            self.assertIn("website_rendered", res.get_data(as_text=True))
            mock_req.render.assert_called_once()
            args, _ = mock_req.render.call_args
            self.assertEqual(
                args[0],
                "enhanced_survey_management.survey_visibility",
            )
            self.assertTrue(
                any(
                    s['title'] == self.survey.title
                    for s in args[1]['survey_list']
                ),
                "Created survey should be present in website survey list",
            )
            self.assertEqual(args[1]['page_name'], 'survey')

    def test_11_many2many_multiple_values_and_review(self):
        """Test saving and reviewing multiple selections on many2many questions."""
        q_m2m = self.env['survey.question'].create({
            'title': 'Many2many Multiple Review',
            'survey_id': self.survey.id,
            'question_type': 'many2many',
            'model_id': self.env.ref('base.model_res_partner').id,
        })
        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey.id,
            'partner_id': self.partner.id,
        })

        user_input._save_lines(q_m2m, ['Partner A', 'Partner B', 'Partner C'])
        line = user_input.user_input_line_ids.filtered(
            lambda rec: rec.question_id == q_m2m,
        )
        self.assertEqual(line.value_many2many, 'Partner A, Partner B, Partner C')
        self.assertEqual(line.display_name, 'Partner A, Partner B, Partner C')

        rendered = str(self.env['ir.qweb']._render(
            'enhanced_survey_management.question_many2many',
            {'question': q_m2m, 'answer_lines': line},
        ))
        self.assertIn('multiple="multiple"', rendered)
        for label in ('Partner A', 'Partner B', 'Partner C'):
            self.assertIn(label, rendered)
