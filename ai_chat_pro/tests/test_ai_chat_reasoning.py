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

import requests

from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_reasoning import _REASONING_MODELS_CACHE, get_reasoning_models

from .test_ai_chat_pro import mock_intent

CONTACT = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': 'Contacts', 'domain': ''}


def mock_openrouter(content, prompt_tokens=120, completion_tokens=30, cost=0.0002):
    """ Patch the calls to OpenRouter, answering ``content`` to the chat completions.
    Return the payloads sent, and the patch. """
    payloads = []

    def openrouter_post(self_, endpoint, payload, usage, api_key=None):
        payloads.append((endpoint, payload))
        usage['ai_called'] = True
        return {
            'choices': [{'message': {'content': content(payload) if callable(content) else content}}],
            'usage': {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens, 'cost': cost},
        }
    return payloads, patch.object(AiChatAssistant, '_openrouter_post', openrouter_post)


@tagged('post_install', '-at_install')
class TestAiChatReasoning(TransactionCase):

    # what the agent understands of the messages of these tests
    INTENTS = {
        'create a contact Mira Rao, mira@example.com': {'intent': 'create', 'target': 'contact'},
        'create a contact Ravi Das': {'intent': 'create', 'target': 'contact'},
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
        cls.user = new_test_user(
            cls.env, login='ai_reasoning_user', groups='base.group_user,base.group_partner_manager,'
                                                       'ai_chat_pro.group_ai_chat_user',
        )

    def _set_reasoning(self, enabled, model_id):
        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.reasoning_openrouter', enabled)
        IrConfigParameter.set_param('ai_chat_pro.reasoning_model', model_id)

    def test_odoo_ai_unless_enabled_with_a_model(self):
        Assistant = self.env['ai.chat.assistant']
        for enabled, model_id in ((False, 'openai/gpt-4o-mini'), (True, False), (True, 'not-a-model')):
            self._set_reasoning(enabled, model_id)
            payloads, mock = mock_openrouter("from OpenRouter")
            with mock, patch.object(AiChatAssistant, '_olg_chat', lambda self_, prompt: "from Odoo AI"):
                self.assertEqual(Assistant._text_chat("Hello"), "from Odoo AI", (enabled, model_id))
            self.assertFalse(payloads, "OpenRouter is only used when enabled, with a model chosen")

    def test_openrouter_model_instead_of_odoo_ai(self):
        self._set_reasoning(True, 'openai/gpt-4o-mini')
        usage = {'prompt_tokens': 10, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False, 'cache': False}
        payloads, mock = mock_openrouter("The best customer is Zeta.")

        def olg_chat(self_, prompt):
            raise AssertionError("Odoo's AI service is not called")
        with mock, patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            answer = self.env['ai.chat.assistant']._text_chat("Who is my best customer?", usage)
        self.assertEqual(answer, "The best customer is Zeta.")
        endpoint, payload = payloads[0]
        self.assertTrue(endpoint.endswith('/chat/completions'))
        self.assertEqual(payload['model'], 'openai/gpt-4o-mini')
        self.assertEqual(payload['messages'], [{'role': 'user', 'content': "Who is my best customer?"}])
        # tokens and cost are counted with the question; the decision model was not called
        self.assertEqual((usage['prompt_tokens'], usage['completion_tokens']), (130, 30))
        self.assertAlmostEqual(usage['cost'], 0.0002)
        self.assertFalse(usage['ai_called'])

        _payloads, mock = mock_openrouter("  ")
        with mock, self.assertRaisesRegex(UserError, "gave no answer"):
            self.env['ai.chat.assistant']._text_chat("Who is my best customer?")

    def test_record_values_read_by_the_openrouter_model(self):
        self._set_reasoning(True, 'openai/gpt-4o-mini')
        payloads, mock = mock_openrouter(json.dumps({'values': {'name': "Mira Rao", 'email': "mira@example.com"}}))
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        with mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [CONTACT]):
            message = Conversation.ask_question(False, "create a contact Mira Rao, mira@example.com")['messages'][1]
        self.assertFalse(message['is_error'], message['content'])
        shown = {field['label']: field['value'] for field in message['result']['fields']}
        self.assertEqual((shown['Name'], shown['Email']), ("Mira Rao", "mira@example.com"))
        self.assertTrue(any(payload['model'] == 'openai/gpt-4o-mini' for _endpoint, payload in payloads))
        self.assertEqual(message['tokens'], 150, "the tokens of the model are counted with the question")
        self.assertEqual(message['text_model'], 'openai/gpt-4o-mini', "the model is shown with the answer")
        self.assertFalse(message['used_olg'])

        # with Odoo's AI service, no model is shown
        self._set_reasoning(False, 'openai/gpt-4o-mini')
        olg_answer = json.dumps({'values': {'name': "Ravi Das"}})
        with patch.object(AiChatAssistant, '_olg_chat', lambda self_, prompt: olg_answer), \
                patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [CONTACT]):
            message = Conversation.ask_question(False, "create a contact Ravi Das")['messages'][1]
        self.assertFalse(message['is_error'], message['content'])
        self.assertFalse(message['text_model'])
        self.assertTrue(message['used_olg'], "Odoo AI is shown with the answer it wrote")

    def test_reasoning_models(self):
        class Response:
            ok = True

            def __init__(self, data):
                self.data = data

            def json(self):
                return {'data': self.data}

            def raise_for_status(self):
                pass

        def model(model_id, inputs, outputs, prompt, completion):
            return {
                'id': model_id, 'name': model_id.upper(),
                'architecture': {'input_modalities': inputs, 'output_modalities': outputs},
                'pricing': {'prompt': prompt, 'completion': completion},
            }

        _REASONING_MODELS_CACHE.clear()
        listed = [
            model('a/expensive', ['text'], ['text'], '0.000003', '0.000015'),
            model('b/cheap', ['text', 'image'], ['text'], '0.0000001', '0.0000004'),
            model('c/free', ['text'], ['text'], '0', '0'),
            model('d/router', ['text'], ['text'], '-1', '-1'),
            model('e/images', ['text'], ['image'], '0.000001', '0.000001'),
            model('f/later:batch', ['text'], ['text'], '0.00000001', '0.00000001'),
            model('g/audio-only', ['audio'], ['text'], '0.000001', '0.000001'),
        ]
        with patch.object(requests, 'get', return_value=Response(listed)):
            reasoning_models = get_reasoning_models()
        self.assertEqual([model_id for model_id, _label in reasoning_models], ['c/free', 'b/cheap', 'a/expensive'])
        labels = dict(reasoning_models)
        self.assertEqual(labels["c/free"], "C/FREE", "a free model says so in its name")
        self.assertIn("$0.10 / $0.40 per M input / output tokens", labels['b/cheap'])
        # listed once an hour
        with patch.object(requests, 'get', side_effect=AssertionError("no call expected")):
            self.assertEqual(get_reasoning_models(), reasoning_models)
        # the settings always offer the model chosen
        self._set_reasoning(True, 'z/chosen')
        selection = self.env['res.config.settings']._get_reasoning_model_selection()
        self.assertEqual(selection[0], ('z/chosen', 'z/chosen'))
        self.assertIn('b/cheap', dict(selection))
        _REASONING_MODELS_CACHE.clear()
