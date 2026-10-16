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

from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant

from .test_ai_chat_pro import mock_intent


def table(heading, rows):
    return {
        'type': 'table', 'model': 'res.partner', 'heading': heading, 'total': len(rows),
        'columns': [{'label': "Name", 'numeric': False}], 'rows': [{'id': False, 'cells': [row]} for row in rows],
    }


@tagged('post_install', '-at_install')
class TestAiChatBrain(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_str('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_bool('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_bool('ai_chat_pro.reasoning_openrouter', False)
        cls.user = new_test_user(cls.env, login='ai_brain_user', groups='base.group_user,ai_chat_pro.group_ai_chat_user')

    def _mock(self, answers, thoughts):
        """ Patch the data tool answering each question with ``answers`` (none: no
        record), and the brain answering in turn ``thoughts``. Return the data questions
        and the prompts of the brain, and the patches. """
        asked, prompts = [], []

        def answer_data(self_, question, previous_plan, usage):
            asked.append(question)
            rows = answers.get(question) or []
            content = f"{question}: {len(rows)} record(s) found." if rows else "No matching record found."
            return {'content': content, 'result': table(question, rows), 'plan': {'question': question}}

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            return json.dumps(thoughts[len(prompts) - 1]) if len(prompts) <= len(thoughts) else "{}"
        return asked, prompts, (patch.object(AiChatAssistant, '_answer_data', answer_data),
                                patch.object(AiChatAssistant, '_olg_chat', olg_chat))

    def _ask(self, question, intent, mocks):
        _understood, intent_mock = mock_intent(**intent)
        with intent_mock, mocks[0], mocks[1]:
            return self.env['ai.chat.conversation'].with_user(self.user).ask_question(False, question)['messages'][1]

    def test_request_answered_step_by_step(self):
        # "the contacts of my biggest customer": the customer first, then the brain asks for its contacts by name
        asked, prompts, mocks = self._mock(
            {"my biggest customer": ["Zeta Big Co"], "contacts of Zeta Big Co": ["Ann", "Bob"]},
            [{'thought': "Now the contacts of that customer.", 'action': 'ask', 'last': True,
              'step': {'q': "contacts of Zeta Big Co", 'names': [{'label': "customer", 'text': "Zeta Big Co"}]}}],
        )
        message = self._ask("the contacts of my biggest customer", {
            'intent': 'query', 'multi_step': True, 'steps': [{'q': "my biggest customer"}]}, mocks)
        self.assertEqual(asked, ["my biggest customer", "contacts of Zeta Big Co"])
        self.assertEqual(len(prompts), 1, "the first step was planned with the understanding, the last ends it")
        self.assertIn("Found: my biggest customer: 1 record(s) found.", prompts[0])
        self.assertIn("Zeta Big Co", prompts[0], "the brain reads the records found")
        self.assertEqual([row['cells'][0] for row in message['result']['rows']], ["Ann", "Bob"])
        self.assertEqual(len(message['thoughts']), 3)
        self.assertIn("Now the contacts of that customer.", message['thoughts'])

    def test_failed_answer_reflected_on(self):
        # nothing found: the brain thinks why, and asks a better question once
        asked, prompts, mocks = self._mock(
            {"contacts of Zeta Retry Co": ["Ann"]},
            [{'thought': "The company may be named in full.", 'retry': {'q': "contacts of Zeta Retry Co"}}],
        )
        message = self._ask("contacts of zeta retry", {'intent': 'query'}, mocks)
        self.assertEqual(asked, ["contacts of zeta retry", "contacts of Zeta Retry Co"])
        self.assertIn("Found: No matching record found.", prompts[0])
        self.assertEqual([row['cells'][0] for row in message['result']['rows']], ["Ann"])
        self.assertEqual(message['thoughts'][0], "The company may be named in full.")
        # a name the brain invents is not asked
        asked, _prompts, mocks = self._mock(
            {}, [{'thought': "Maybe this.", 'retry': {'q': "contacts of X", 'names': [{'label': "c", 'text': "Invented"}]}}])
        message = self._ask("contacts of nobody known", {'intent': 'query'}, mocks)
        self.assertEqual(asked, ["contacts of nobody known", "contacts of X"])
        self.assertFalse(message['result']['rows'])

    def test_thinking_disabled(self):
        settings = self.env['res.config.settings'].create({})
        self.assertTrue(settings.ai_chat_pro_agent_thinking, "on by default")
        settings.ai_chat_pro_agent_thinking = False
        settings.execute()
        self.assertFalse(self.env['res.config.settings'].create({}).ai_chat_pro_agent_thinking)
        asked, prompts, mocks = self._mock({}, [{'thought': "x", 'retry': {'q': "other"}}])
        message = self._ask("contacts of nobody", {'intent': 'query', 'multi_step': True,
                                                   'steps': [{'q': "first step"}]}, mocks)
        self.assertEqual(asked, ["contacts of nobody"])
        self.assertFalse(prompts)
        self.assertFalse(message['thoughts'])
