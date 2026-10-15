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
import io
import json
from unittest.mock import patch

from reportlab.pdfgen import canvas

from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_document import DOCUMENT_MODEL, _get_pdf_text

from .test_ai_chat_pro import mock_intent

# the contacts menu creating its contacts as buyers: its defaults apply to the record created
CONTACTS = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': 'Contacts', 'domain': '',
            'context': "{'default_function': 'Buyer'}"}


def make_pdf(lines):
    output = io.BytesIO()
    pdf = canvas.Canvas(output)
    for index, line in enumerate(lines):
        pdf.drawString(72, 760 - 18 * index, line)
    pdf.showPage()
    pdf.save()
    return output.getvalue()


@tagged('post_install', '-at_install')
class TestAiChatDocument(TransactionCase):

    # what the agent understands of the messages of these tests
    INTENTS = {
        'create a contact from the attached PDF': {'intent': 'create', 'target': 'contact'},
        'what is the number of this invoice?': {'intent': 'file'},
    }

    def setUp(self):
        super().setUp()
        self.understood, intent_mock = mock_intent(self.INTENTS)
        self.startPatcher(intent_mock)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_param('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_param('ai_chat_pro.allow_create', 'True')
        IrConfigParameter.set_param('ai_chat_pro.reasoning_openrouter', False)
        cls.user = new_test_user(
            cls.env, login='ai_document_user', groups='base.group_user,base.group_partner_manager,'
                                                      'ai_chat_pro.group_ai_chat_user',
        )
        cls.Conversation = cls.env['ai.chat.conversation'].with_user(cls.user)
        cls.card = make_pdf([
            "BUSINESS CARD", "Zeta Doc Traders Pvt Ltd", "Email: hello@zetadoc.example.com", "City: Kochi",
        ])

    def _upload(self, raw, name):
        return self.Conversation.upload_chat_attachment(name, base64.b64encode(raw).decode())

    def test_pdf_text(self):
        text = _get_pdf_text(self.card)
        self.assertIn("Zeta Doc Traders Pvt Ltd", text)
        self.assertEqual(_get_pdf_text(b"not a pdf"), "")
        self.assertEqual(self._upload(self.card, "card.pdf")['mimetype'], 'application/pdf')
        with self.assertRaisesRegex(UserError, "PDFs and pictures"):
            self._upload(b"MZ", "setup.exe")

    def test_create_record_from_pdf(self):
        attachment = self._upload(self.card, "card.pdf")
        prompts = []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            if "Choose which record the request creates" in prompt:
                return '{"option":"option_0"}'
            return json.dumps({'values': {'name': "Zeta Doc Traders Pvt Ltd", 'email': "hello@zetadoc.example.com",
                                          'city': "Kochi", 'website': "https://made.up.example.com"}})
        with patch.object(AiChatAssistant, '_olg_chat', olg_chat), \
                patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [CONTACTS]):
            message = self.Conversation.ask_question(
                False, "create a contact from the attached PDF", False, [attachment['id']])['messages'][1]
        self.assertFalse(message['is_error'], message['content'])
        draft = message['result']
        self.assertEqual(draft['document'], {'name': "card.pdf", 'id': attachment['id']})
        shown = {field['label']: field['value'] for field in draft['fields']}
        self.assertEqual((shown['Name'], shown['Email'], shown['City']),
                         ("Zeta Doc Traders Pvt Ltd", "hello@zetadoc.example.com", "Kochi"))
        self.assertNotIn('Website', shown, "a value the document does not hold is not kept")
        self.assertIn('I read "card.pdf"', message['content'])
        # the AI filling the values reads the text of the document
        values_prompt = next(prompt for prompt in prompts if "You fill in a new record" in prompt)
        self.assertIn("BUSINESS CARD", values_prompt)
        self.assertEqual(draft['context'], {'default_function': 'Buyer'})

        created = self.Conversation.create_draft_record(message['id'])['result']
        partner = self.env['res.partner'].browse(created['res_id'])
        self.assertEqual((partner.name, partner.city), ("Zeta Doc Traders Pvt Ltd", "Kochi"))
        self.assertEqual(partner.function, "Buyer", "the defaults of the menu apply to the record created")

    def test_own_company_is_no_partner(self):
        # the AI may take the company of the user for the other party of the document: never kept
        company = self.env.company.partner_id
        attachment = self._upload(make_pdf(["DELIVERY NOTE", f"To: {company.name}", "From: Zeta Doc Sender"]), "note.pdf")

        def olg_chat(self_, prompt):
            if "Choose which record the request creates" in prompt:
                return '{"option":"option_0"}'
            return json.dumps({'values': {'name': "Zeta Doc Sender", 'parent_id': company.name}})
        with patch.object(AiChatAssistant, '_olg_chat', olg_chat), \
                patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [CONTACTS]):
            draft = self.Conversation.ask_question(
                False, "create a contact from the attached PDF", False, [attachment['id']])['messages'][1]['result']
        self.assertNotIn('parent_id', draft['values'])
        self.assertTrue(any("your own company" in warning for warning in draft['warnings']))

    def test_scan_read_by_a_model(self):
        # a PDF without text (a scan): read by a model of OpenRouter, with the key of the assistant
        scan = make_pdf([])
        attachment = self._upload(scan, "scan.pdf")
        payloads = []

        def openrouter_post(self_, endpoint, payload, usage, api_key=None):
            payloads.append(payload)
            usage['ai_called'] = True
            return {'choices': [{'message': {'content': "Invoice INV-77 from Zeta Scan Co, total 500"}}],
                    'usage': {'prompt_tokens': 900, 'completion_tokens': 40, 'cost': 0.0003}}
        with patch.object(AiChatAssistant, '_openrouter_post', openrouter_post), \
                patch.object(AiChatAssistant, '_olg_chat', lambda self_, prompt: "It is invoice INV-77."):
            message = self.Conversation.ask_question(
                False, "what is the number of this invoice?", False, [attachment['id']])['messages'][1]
        self.assertEqual(message['content'], "It is invoice INV-77.")
        content = payloads[0]['messages'][0]['content']
        self.assertEqual(payloads[0]['model'], DOCUMENT_MODEL)
        self.assertTrue(content[1]['file']['file_data'].startswith("data:application/pdf;base64,"))
        self.assertEqual(message['tokens'], 940, "reading the scan is counted with the question")
        self.assertEqual(message['text_model'], DOCUMENT_MODEL)

        # without the key of OpenRouter, a scan can not be read
        self.env['ir.config_parameter'].sudo().set_param('ai_chat_pro.openrouter_api_key', False)
        attachment = self._upload(scan, "scan2.pdf")
        message = self.Conversation.ask_question(
            False, "what is the number of this invoice?", False, [attachment['id']])['messages'][1]
        self.assertTrue(message['is_error'])
        self.assertIn("needs the OpenRouter API key", message['content'])
