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

from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_creator import AiChatAssistant as AiChatCreator
from odoo.addons.ai_chat_pro.models.ai_chat_deep import MAX_DEEP_ITEMS, _clean_analysis

from .test_ai_chat_pro import mock_intent

ANALYSIS = {
    'verdict': "Promote Office Chair to your top 3 customers of desks.",
    'confidence': 'high',
    'summary': "Office Chair sells half as much as last year while desks grow.",
    'findings': ["Office Chair: 12 units this year, 25 last year", "Desks: +40%"],
    'recommendations': [
        {'action': "Bundle Office Chair with desks", 'reason': "Desk buyers need chairs", 'impact': "+20 units a quarter"},
        "Train the sales team on chairs",
    ],
    'risks': ["Only 2 years of data"],
    'next_steps': ["Prepare the bundle price this week"],
}


@tagged('post_install', '-at_install')
class TestAiChatDeep(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_str('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_bool('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_bool('ai_chat_pro.allow_create', True)
        IrConfigParameter.set_bool('ai_chat_pro.deep_analysis', True)
        IrConfigParameter.set_bool('ai_chat_pro.reasoning_openrouter', False)
        cls.user = new_test_user(
            cls.env, login='ai_deep_user', groups='base.group_user,base.group_partner_manager,'
                                                  'ai_chat_pro.group_ai_chat_user',
        )

    def _mock(self, planned, analysis=ANALYSIS, data=True):
        """ Patch Odoo's AI service planning and writing the analysis, and the answers to
        the data questions. Return the prompts, the data questions asked, and the patches. """
        prompts, asked = [], []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            if "You prepare the analysis" in prompt:
                return json.dumps({'steps': planned})
            return analysis if isinstance(analysis, str) else "```json\n" + json.dumps(analysis) + "\n```"

        def answer_data(self_, question, previous_plan, usage):
            asked.append(question)
            if not data:
                return {'content': "Nothing found", 'result': {'type': 'table', 'rows': [], 'columns': []}}
            return {'content': "", 'result': {
                'type': 'table', 'heading': f"Data of {question}", 'tags': ["This year"], 'total': 30,
                'columns': [{'label': "Product"}, {'label': "Quantity"}],
                'rows': [{'cells': [f"Product {index}", str(index)]} for index in range(30)],
            }}
        return prompts, asked, [
            patch.object(AiChatAssistant, '_olg_chat', olg_chat),
            patch.object(AiChatAssistant, '_answer_data', answer_data),
        ]

    def _ask(self, question, deep=True, intent=None):
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        _understood, intent_mock = mock_intent(**(intent or {'intent': 'query'}))
        with intent_mock:
            return Conversation.ask_question(False, question, deep)['messages'][1]

    def test_deep_analysis(self):
        question = "How can I increase the sales of Office Chair?"
        prompts, asked, mocks = self._mock([
            "sales amount per month of Office Chair this year", "top 10 customers of Office Chair",
        ])
        with mocks[0], mocks[1]:
            message = self._ask(question)
        self.assertFalse(message['is_error'], message['content'])
        self.assertEqual(message['source'], 'deep')
        self.assertTrue(message['used_olg'], "Odoo AI planned and wrote the analysis")
        # the question itself, then the data questions planned
        self.assertEqual(asked, [
            question, "sales amount per month of Office Chair this year", "top 10 customers of Office Chair",
        ])
        result = message['result']
        self.assertEqual(result['type'], 'analysis')
        self.assertEqual(result['verdict'], ANALYSIS['verdict'])
        self.assertEqual(result['confidence'], 'high')
        self.assertEqual(result['recommendations'][1], {'action': "Train the sales team on chairs", 'reason': '', 'impact': ''})
        self.assertEqual(len(result['datasets']), 3)
        self.assertEqual(len(result['datasets'][0]['rows']), 10, "a few rows are shown with the answer")
        self.assertIn(ANALYSIS['verdict'], message['content'])
        # the AI reads a part of each dataset, and is told how to weigh decisions about people
        final_prompt = prompts[-1]
        self.assertIn("first 15 of 30", final_prompt)
        self.assertIn("never personal traits", final_prompt)
        self.assertIn(question, final_prompt)

    def test_deep_analysis_disabled(self):
        self.env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.deep_analysis', False)
        prompts, asked, mocks = self._mock(["sales per month"])
        with mocks[0], mocks[1]:
            message = self._ask("How can I increase the sales of Office Chair?", intent={'intent': 'query', 'terms': ["sales"]})
            data = self.env['ai.chat.conversation'].with_user(self.user).get_chat_data()
        self.assertFalse(data['deep_analysis'])
        self.assertEqual(asked, ["How can I increase the sales of Office Chair?"], "answered as a usual question")
        self.assertFalse(prompts)
        self.assertNotEqual(message['result'].get('type'), 'analysis')

    def test_create_request_is_no_analysis(self):
        prompts, asked, mocks = self._mock(["anything"])
        with mocks[0], mocks[1], patch.object(AiChatCreator, '_choose_create_model', lambda *args, **kwargs: None):
            message = self._ask("create a contact Deep Contact", intent={'intent': 'create', 'target': 'contact'})
        self.assertIn("I can not create a contact", message['content'])
        self.assertFalse(asked, "no data read for a record that can not be created")
        self.assertFalse([prompt for prompt in prompts if "You prepare the analysis" in prompt])

    def test_deep_analysis_without_data(self):
        _prompts, _asked, mocks = self._mock(["sales per month"], data=False)
        with mocks[0], mocks[1]:
            message = self._ask("Which employee should I promote?")
        self.assertFalse(message['result'])
        self.assertIn("could not find data", message['content'])

    def test_deep_analysis_when_the_ai_is_unavailable(self):
        # every data question fails (no API key, no credit): the reason is shown, not "no data"
        def answer_data(self_, question, previous_plan, usage):
            raise UserError("The AI assistant is not configured yet")
        _prompts, _asked, mocks = self._mock(["sales per month"])
        with mocks[0], patch.object(AiChatAssistant, '_answer_data', answer_data):
            message = self._ask("How can I increase the sales of Office Chair?")
        self.assertTrue(message['is_error'])
        self.assertIn("not configured", message['content'])

    def test_depth_decided_by_the_decision_model(self):
        # a deep analysis only when enabled, and the decision model confident enough; an explanation else
        Assistant = self.env['ai.chat.assistant'].with_user(self.user)
        self.assertEqual(Assistant._choose_depth({'depth': 'deep', 'depth_confidence': 0.9}, {}), 'deep')
        self.assertEqual(Assistant._choose_depth({'depth': 'deep', 'depth_confidence': 0.3}, {}), 'explain')
        self.assertEqual(Assistant._choose_depth({'depth': 'data', 'depth_confidence': 0.9}, {}), 'data')
        self.assertEqual(Assistant._choose_depth({'reasoning': True}, {}), 'explain', "plans cached before")
        self.env['ir.config_parameter'].sudo().set_float('ai_chat_pro.deep_confidence', 0.95)
        self.assertEqual(Assistant._choose_depth({'depth': 'deep', 'depth_confidence': 0.9}, {}), 'explain')
        self.assertEqual(Assistant.with_context(ai_chat_data_only=True)._choose_depth(
            {'depth': 'deep', 'depth_confidence': 1.0}, {}), 'data', "the data of an analysis is only read")
        self.env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.deep_analysis', False)
        self.assertEqual(Assistant._choose_depth({'depth': 'deep', 'depth_confidence': 0.9}, {}), 'explain')

    def test_agent_switches_to_a_deep_analysis(self):
        # not asked by the user: the decision model chose a deep analysis, the agent planned its data
        question = "Should I stop selling Office Chair?"
        prompts, asked, mocks = self._mock([])
        first = {'type': 'table', 'heading': "Office Chair sales", 'tags': [], 'total': 1,
                 'columns': [{'label': "Product"}, {'label': "Quantity"}], 'rows': [{'cells': ["Office Chair", "3"]}]}
        super_answer = mocks[1].new

        def answer_data(self_, data_question, previous_plan, usage):
            if not self_.env.context.get('ai_chat_data_only'):
                asked.append(data_question)
                return {'content': "", 'result': first, 'plan': {'question': question}, 'escalate': True}
            return super_answer(self_, data_question, previous_plan, usage)
        intent = {'intent': 'query', 'advice': True, 'steps': [{'q': "stock of Office Chair"}]}
        with mocks[0], patch.object(AiChatAssistant, '_answer_data', answer_data):
            message = self._ask(question, deep=False, intent=intent)
        self.assertEqual(message['source'], 'deep')
        self.assertEqual(asked, [question, "stock of Office Chair"], "the data found first is not read again")
        self.assertEqual(len(message['result']['datasets']), 2)
        self.assertFalse([prompt for prompt in prompts if "You prepare the analysis" in prompt],
                         "the data questions the agent planned are used")

    def test_clean_analysis(self):
        cleaned = _clean_analysis(None, "Sell more chairs.")
        self.assertEqual((cleaned['summary'], cleaned['confidence'], cleaned['findings']), ("Sell more chairs.", 'low', []))
        cleaned = _clean_analysis({
            'verdict': "  Do   it ", 'confidence': 'certain', 'findings': ["a"] * 20 + [None, ""],
            'recommendations': [{'reason': "no action"}, 7], 'risks': "not a list",
        }, "")
        self.assertEqual(cleaned['verdict'], "Do it")
        self.assertEqual(cleaned['confidence'], 'medium')
        self.assertEqual(len(cleaned['findings']), MAX_DEEP_ITEMS['findings'])
        self.assertEqual((cleaned['recommendations'], cleaned['risks']), ([], []))
