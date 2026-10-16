# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_report import REPORT_REF

from .test_ai_chat_pro import mock_decisions

# a 1x1 PNG image
PNG = base64.b64encode(
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    b'\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
).decode()
CANDIDATES = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]


@tagged('post_install', '-at_install')
class TestAiChatReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_str('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_bool('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_bool('ai_chat_pro.chart_olg', False)
        cls.user = new_test_user(cls.env, login='ai_report_user', groups='base.group_user,ai_chat_pro.group_ai_chat_user')
        cls.other_user = new_test_user(cls.env, login='ai_report_other',
                                       groups='base.group_user,ai_chat_pro.group_ai_chat_user')
        cls.env['res.partner'].create([{'name': "Report Partner Alpha"}, {'name': "Report Partner Beta"}])

    def _ask(self, question, **decisions):
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        _calls, mock = mock_decisions(**decisions)
        with mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: CANDIDATES):
            answer = Conversation.ask_question(False, question)
        return self.env['ai.chat.message'].with_user(self.user).browse(answer['messages'][1]['id'])

    def _html(self, message, data=None):
        html, _type = self.env['ir.actions.report'].with_user(self.user)._render_qweb_html(
            REPORT_REF, message.ids, data=data or {},
        )
        return html.decode()

    def test_report_of_a_table(self):
        message = self._ask("list the report partners", mode='list', sort='name', direction='asc',
                            names_record=True, name_field='name')
        self.assertTrue(message._can_print_report())
        html = self._html(message, {'chart': f"data:image/png;base64,{PNG}"})
        # the question of the user is not printed: without Odoo AI, the report is titled after its data
        self.assertNotIn("list the report partners", html.lower())
        self.assertEqual(message._get_report_title(), message.result['heading'])
        self.assertIn(message.result['heading'], html)
        self.assertIn("Report Partner Alpha", html)
        self.assertIn(f"data:image/png;base64,{PNG}", html)
        self.assertIn(self.user.name, html)

    def test_report_of_key_figures(self):
        message = self._ask("how many report partners", mode='count')
        self.assertEqual(message.result['type'], 'value')
        html = self._html(message)
        self.assertIn(str(message.result['value']), html)

    def test_no_report_without_data(self):
        error = self.env['ai.chat.message'].create({
            'conversation_id': self.env['ai.chat.conversation'].with_user(self.user).create({}).id,
            'role': 'assistant', 'content': "Oops", 'is_error': True,
        })
        self.assertFalse(error._can_print_report())
        empty = self._ask("list the report partners", mode='list', sort='name', direction='asc')
        empty.sudo().result = dict(empty.result, rows=[], total=0)
        self.assertFalse(empty._can_print_report(), "a table without any record makes no report")
        with self.assertRaisesRegex(UserError, "no data"):
            error.with_user(self.user)._render_pdf_report()

    def test_summary_written_once_by_odoo_ai(self):
        message = self._ask("list the report partners", mode='list', sort='name', direction='asc')
        self.env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.use_olg', True)
        prompts = []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            return "Title: **Contacts by Name**\nThe contacts are listed by name.\n- Alpha comes first\n- Beta follows"

        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            html = self._html(message)
            self._html(message)
        self.assertEqual(len(prompts), 1, "the summary is written once, then reused")
        self.assertIn("Report Partner Alpha", prompts[0], "the summary is written from the data of the answer")
        self.assertIn("The contacts are listed by name.", html)
        self.assertIn("Alpha comes first", html)
        self.assertEqual(message.report_summary['insights'], ["Alpha comes first", "Beta follows"])
        # titled by Odoo AI after the data, never with the question of the user
        self.assertEqual(message._get_report_title(), "Contacts by Name")
        self.assertIn("Contacts by Name", html)
        self.assertNotIn("list the report partners", html.lower())
        self.assertTrue(message._get_report_file_name().startswith("Contacts_by_Name_"))

    def test_summary_without_odoo_ai(self):
        message = self._ask("list the report partners", mode='list', sort='name', direction='asc')
        self.env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.use_olg', True)

        def olg_chat(self_, prompt):
            raise UserError("You do not have enough credits to use Odoo's AI service.")

        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            summary = message._get_report_summary()
        self.assertEqual(summary, {'text': message.content, 'insights': []})
        self.assertFalse(message.report_summary, "a summary that could not be written is tried again")

    def test_pdf_printed_by_the_report_engine(self):
        message = self._ask("list the report partners", mode='list', sort='name', direction='asc')
        printed = []

        def render_qweb_pdf(self_, report_ref, res_ids=None, data=None):
            printed.append((report_ref, res_ids, data, self_.env.context.get('landscape')))
            return b'%PDF-1.7 report', 'pdf'

        with patch.object(type(self.env['ir.actions.report']), '_render_qweb_pdf', render_qweb_pdf):
            file_name, content = message._render_pdf_report(chart=f"data:image/png;base64,{PNG}")
        self.assertEqual(content, b'%PDF-1.7 report')
        self.assertTrue(file_name.endswith('.pdf'))
        report_ref, res_ids, data, landscape = printed[0]
        self.assertEqual((report_ref, res_ids), (REPORT_REF, message.ids))
        self.assertEqual(data['chart'], f"data:image/png;base64,{PNG}")
        self.assertFalse(landscape)

        # a wide table is printed on a landscape page
        result = dict(message.result, columns=[{'label': f"C{i}", 'numeric': False} for i in range(8)])
        message.sudo().result = result
        with patch.object(type(self.env['ir.actions.report']), '_render_qweb_pdf', render_qweb_pdf):
            message._render_pdf_report()
        self.assertTrue(printed[-1][3])

    def test_report_access_and_chart_checks(self):
        message = self._ask("list the report partners", mode='list', sort='name', direction='asc')
        with self.assertRaises(AccessError):
            message.with_user(self.other_user)._render_pdf_report()
        with self.assertRaises(AccessError):
            self.env['ir.actions.report'].with_user(self.other_user)._render_qweb_html(REPORT_REF, message.ids)
        with self.assertRaisesRegex(UserError, "could not be read"):
            message._render_pdf_report(chart="data:image/png;base64,not base64!")
        with self.assertRaisesRegex(UserError, "PNG"):
            message._render_pdf_report(chart=base64.b64encode(b"<svg onload='alert(1)'/>").decode())

    def test_report_without_pdf_engine(self):
        message = self._ask("list the report partners", mode='list', sort='name', direction='asc')
        Report = type(self.env['ir.actions.report'])
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        with patch.object(Report, 'get_pdf_engine_state', lambda self_, engine: 'install'):
            self.assertFalse(Conversation.get_chat_data()['pdf_engine'], "the chat prints reports from the browser")
        with patch.object(Report, 'get_pdf_engine_state', lambda self_, engine: 'ok'):
            self.assertTrue(Conversation.get_chat_data()['pdf_engine'])
        # the same report, as a page to print
        html = message._render_html_report(chart=f"data:image/png;base64,{PNG}").decode()
        self.assertNotIn("list the report partners", html.lower())
        self.assertIn(f"data:image/png;base64,{PNG}", html)
        with self.assertRaises(AccessError):
            message.with_user(self.other_user)._render_html_report()
