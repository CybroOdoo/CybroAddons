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

import json
from unittest.mock import patch

from odoo import fields
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.exceptions import UserError

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_commands import AiChatAssistant as AiChatCommands
from odoo.addons.ai_chat_pro.models.ai_chat_report import AiChatMessage


@tagged('post_install', '-at_install')
class TestAiChatCommands(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_param('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_param('ai_chat_pro.reasoning_openrouter', False)
        cls.user = new_test_user(
            cls.env, login='ai_command_user', groups='base.group_user,base.group_partner_manager,'
                                                    'ai_chat_pro.group_ai_chat_user',
        )
        cls.partner = cls.env['res.partner'].create({
            'name': "Zeta Explain Co", 'is_company': True, 'email': "hi@zetaexplain.example.com", 'city': "Kochi",
        })
        cls.partner.message_post(body="Asked for a quote on 40 chairs", message_type='comment')
        todo = cls.env.ref('mail.mail_activity_data_todo')
        today = fields.Date.context_today(cls.partner)
        cls.overdue = cls.partner.activity_schedule(
            activity_type_id=todo.id, summary="Send the quote", user_id=cls.user.id,
            date_deadline=fields.Date.add(today, days=-2))
        done = cls.partner.activity_schedule(
            activity_type_id=todo.id, summary="First call", user_id=cls.user.id, date_deadline=today)
        done.action_done()
        cls.Conversation = cls.env['ai.chat.conversation'].with_user(cls.user)

    def _ask(self, question, mentions=None, answer=None):
        prompts = []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            return json.dumps(answer if answer is not None else {
                'overview': "Zeta Explain Co is a company in Kochi waiting for a quote.",
                'key_points': ["Based in Kochi"], 'history': ["Asked for a quote"],
                'attention': ["The quote is overdue"],
            })
        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            message = self.Conversation.ask_question(False, question, False, None, mentions)['messages'][1]
        return message, prompts

    def test_commands_offered(self):
        commands = self.Conversation.get_chat_data(False)['commands']
        self.assertEqual([command['name'] for command in commands], ['explain', 'report'])

    def test_explain(self):
        message, prompts = self._ask("/explain @Zeta Explain Co", [{'model': 'res.partner', 'id': self.partner.id}])
        result = message['result']
        self.assertEqual((result['type'], result['model'], result['id']), ('explain', 'res.partner', self.partner.id))
        self.assertEqual(result['overview'], "Zeta Explain Co is a company in Kochi waiting for a quote.")
        self.assertEqual(result['attention'], ["The quote is overdue"])
        # the activities as Odoo holds them: the planned one, then the one done
        self.assertEqual([(a['summary'], a['state']) for a in result['activities']],
                         [("Send the quote", 'overdue'), ("First call", 'done')])
        # the chatter: the message, and the change of the tracked email, read by the AI
        texts = [entry['text'] for entry in result['history']]
        self.assertIn("Asked for a quote on 40 chairs", texts)
        prompt = prompts[0]
        self.assertIn("Asked for a quote on 40 chairs", prompt)
        self.assertIn("overdue: To-Do \"Send the quote\"", prompt)
        self.assertIn("Email: hi@zetaexplain.example.com", prompt)
        # the fields of its form, not the technical ones
        self.assertNotIn("Normalized Email", prompt)

    def test_explain_without_ai(self):
        # the AI fails: the activities and the chatter are still shown
        message, _prompts = self._ask("/explain @Zeta Explain Co", [{'model': 'res.partner', 'id': self.partner.id}],
                                      answer={})
        self.assertFalse(message['result']['overview'])
        self.assertTrue(message['result']['note'])
        self.assertEqual(len(message['result']['activities']), 2)

    def test_explain_needs_a_record(self):
        message, prompts = self._ask("/explain")
        self.assertTrue(message['is_error'])
        self.assertIn("Mention it with @", message['content'])
        self.assertFalse(prompts)

    def test_unknown_command(self):
        message, _prompts = self._ask("/summon the books")
        self.assertIn("There is no command \"/summon\"", message['content'])
        self.assertIn("/explain, /report", message['content'])


@tagged('post_install', '-at_install')
class TestAiChatReportCommand(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login='ai_report_user', groups='base.group_user,base.group_partner_manager,'
                                                   'ai_chat_pro.group_ai_chat_user',
        )
        cls.partner = cls.env['res.partner'].create({'name': "Zeta Report Co", 'is_company': True})
        cls.env['ir.ui.view'].create({
            'name': "ai_chat_pro.test_partner_report", 'type': 'qweb', 'key': 'ai_chat_pro.test_partner_report',
            'arch': '<t t-name="ai_chat_pro.test_partner_report"><t t-call="web.html_container">'
                    '<t t-foreach="docs" t-as="o"><p class="zeta-report">Partner <t t-out="o.name"/></p></t>'
                    '</t></t>',
        })
        Report = cls.env['ir.actions.report']
        # the reports of the Print menu of contacts: the first is the default one
        cls.default, cls.labels, cls.restricted = Report.create([{
            'name': name, 'model': 'res.partner', 'report_type': 'qweb-pdf',
            'report_name': 'ai_chat_pro.test_partner_report', 'print_report_name': "'Sheet - %s' % object.name",
            'group_ids': groups,
        } for name, groups in (
            ("Zeta Partner Sheet", False), ("Zeta Address Labels", False),
            ("Zeta Secret Sheet", [(6, 0, cls.env.ref('base.group_system').ids)]),
        )])
        (cls.default + cls.labels + cls.restricted).create_action()
        cls.Conversation = cls.env['ai.chat.conversation'].with_user(cls.user)
        cls.mention = [{'model': 'res.partner', 'id': cls.partner.id}]

    def _ask(self, question, pdf_engine=False):
        def render_pdf(self_, report_ref, res_ids=None, data=None):
            return b'%PDF-1.4 zeta', 'pdf'
        with patch.object(AiChatMessage, '_has_pdf_engine', lambda self_: pdf_engine), \
                patch.object(type(self.env['ir.actions.report']), '_render_qweb_pdf', render_pdf):
            return self.Conversation.ask_question(False, question, False, None, self.mention)['messages'][1]

    def _reports(self, result):
        return [result['report']['name']] + [other['name'] for other in result['others']
                                             if other['name'].startswith("Zeta")]

    def test_default_report(self):
        result = self._ask("/report @Zeta Report Co")['result']
        self.assertEqual((result['type'], result['model'], result['id']), ('print', 'res.partner', self.partner.id))
        # the first report of the Print menu, without the one of a group the user is not in
        self.assertEqual(self._reports(result), ["Zeta Partner Sheet", "Zeta Address Labels"])
        self.assertFalse(result['pdf_engine'])
        self.assertNotIn('attachment_id', result)

    def test_report_named(self):
        result = self._ask("/report @Zeta Report Co address labels")['result']
        self.assertEqual(result['report']['name'], "Zeta Address Labels")

    def test_pdf_printed(self):
        message = self._ask("/report @Zeta Report Co", pdf_engine=True)
        result = message['result']
        attachment = self.env['ir.attachment'].with_user(self.user).browse(result['attachment_id'])
        self.assertEqual((attachment.res_model, attachment.res_id), ('ai.chat.message', message['id']))
        self.assertEqual(attachment.raw, b'%PDF-1.4 zeta')
        self.assertEqual(result['file_name'], "Sheet - Zeta Report Co.pdf")

    def test_report_page(self):
        # without the PDF engine: the page of the report, printed by the browser
        Assistant = self.env['ai.chat.assistant'].with_user(self.user)
        partner = self.partner.with_user(self.user)
        name, content, mimetype = Assistant._render_record_report(self.default, partner, pdf=False)
        self.assertEqual((name, mimetype), ("Sheet - Zeta Report Co.html", 'text/html'))
        self.assertIn(b"Partner Zeta Report Co", content)
        # a report of a group the user is not in, or of another model, is not printed
        with self.assertRaises(UserError):
            Assistant._render_record_report(self.restricted, partner, pdf=False)

    def test_no_report(self):
        (self.default + self.labels + self.restricted).unlink_action()
        with patch.object(AiChatCommands, '_get_record_reports', lambda self_, record: self.env['ir.actions.report']):
            message = self._ask("/report @Zeta Report Co")
        self.assertTrue(message['is_error'])
        self.assertIn("no report to print", message['content'])

    def test_report_needs_a_record(self):
        self.mention = []
        message = self._ask("/report")
        self.assertIn("Mention it with @", message['content'])
