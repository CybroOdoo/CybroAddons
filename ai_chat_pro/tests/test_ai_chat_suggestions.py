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
from odoo.addons.ai_chat_pro.models.ai_chat_suggestions import _clean_suggestions

from .test_ai_chat_pro import mock_decisions, mock_intent

CONTACT = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': 'Contacts', 'domain': ''}
COMPANY = {'model': 'res.company', 'label': 'Companies', 'score': 8.5, 'path': 'Companies', 'domain': ''}


@tagged('post_install', '-at_install')
class TestAiChatSuggestions(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_param('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_param('ai_chat_pro.allow_create', 'True')
        IrConfigParameter.set_param('ai_chat_pro.reasoning_openrouter', False)
        cls.user = new_test_user(
            cls.env, login='ai_suggest_user', groups='base.group_user,base.group_partner_manager,'
                                                     'ai_chat_pro.group_ai_chat_user',
        )

    def _ask(self, question, candidates=(CONTACT,), suggestions=(), values=None, decide=None, intent=None,
             **decisions):
        prompts = []
        _understood, intent_mock = mock_intent(**(intent or {}))

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            if "clearer requests the user may click" in prompt:
                return json.dumps({'suggestions': list(suggestions)})
            return json.dumps({'values': values or {}})
        _calls, mock = mock_decisions(**decisions)
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        with intent_mock, patch.object(AiChatAssistant, '_olg_chat', olg_chat), \
                patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: list(candidates)), \
                (patch.object(AiChatAssistant, '_decide', decide) if decide else mock):
            message = Conversation.ask_question(False, question)['messages'][1]
        return message, [prompt for prompt in prompts if "clearer requests the user may click" in prompt]

    def test_no_data(self):
        message, prompts = self._ask("zorblax figures", candidates=(), suggestions=[
            "List the sales orders", "list the sales orders", "x" * 200, "Show this month's invoices",
        ])
        self.assertIn("could not find any data", message['content'])
        self.assertEqual(message['suggestions'], ["List the sales orders", "Show this month's invoices"])
        self.assertIn("No data of Odoo matched", prompts[0])

    def test_create_or_question(self):
        # the agent reads whether "generate" asks to create: no pattern of verbs, no doubt to offer
        message, prompts = self._ask("generate a contact Zeta Gen", suggestions=["List the contacts"],
                                     values={'name': "Zeta Gen"}, intent={'intent': 'create', 'target': "contact"})
        self.assertEqual(message['result']['type'], 'draft')
        self.assertFalse(message['suggestions'])
        self.assertFalse(prompts)
        message, _prompts = self._ask("generate a contact report", suggestions=["List the contacts"],
                                      intent={'intent': 'query'}, mode='list')
        self.assertNotEqual((message['result'] or {}).get('type'), 'draft')

    def test_uncertain_choice(self):
        def decide(confidence):
            def _decide(self_, state, questions, usage, api_key=None, ai_model=None):
                usage['ai_called'] = True
                if 'data' in questions:
                    return {'data': {'type': 'choice', 'choice': 'option_1', 'confidence': confidence}}
                return {'mode': {'type': 'choice', 'choice': 'list', 'confidence': 0.9}}
            return _decide
        message, prompts = self._ask("our partners overview", candidates=(CONTACT, COMPANY),
                                     suggestions=["List the contacts"], decide=decide(0.4))
        self.assertEqual(message['suggestions'], ["List the contacts"])
        self.assertIn("It may also be about", prompts[0])
        # a confident choice: no suggestion, and no request for them
        message, prompts = self._ask("our partners overview list", candidates=(CONTACT, COMPANY),
                                     suggestions=["List the contacts"], decide=decide(0.95))
        self.assertFalse(message['suggestions'])
        self.assertFalse(prompts)

    def test_clean_suggestions(self):
        self.assertEqual(
            _clean_suggestions(['"list contacts"', "List contacts.", "", "Count leads", "a", "b", "c"], "count leads?"),
            ["List contacts", "A", "B", "C"],
        )

    def test_examples_from_the_apps_of_the_user(self):
        # no data named in the code: the examples and the apps are the user's own menus
        settings = self.env.ref('base.menu_administration').name
        catalog = (
            ('res.partner', "Contact", (), (("Zeta Sales/Customers", '', '', False, ()),
                                            ("Zeta Billing/Customers", '', '', False, ()))),
            ('res.currency', "Currency", (), (("Zeta Billing/Configuration/Currencies", '', '', False, ()),)),
            ('res.company', "Companies", (), ((f"{settings}/Companies", '', '', False, ()),)),
        )
        Assistant = self.env['ai.chat.assistant'].with_user(self.user)
        with patch.object(AiChatAssistant, '_get_model_catalog', lambda self_: catalog):
            self.assertEqual(Assistant._get_app_names(), ["Zeta Sales", "Zeta Billing"], "no settings")
            examples = Assistant._get_example_questions()
            mention_models = [name for name, _label in Assistant._get_mention_models()]
        self.assertEqual(examples['export'], "List the 10 latest customers")
        self.assertEqual(examples['create'], "Create a customer for ", "named as the menu names them")
        self.assertIn("List the 10 latest customers", examples['others'])
        self.assertEqual(mention_models, ['res.partner', 'res.currency'], "the most reached first, no settings")
        # no app: no example, the landing page keeps its own
        with patch.object(AiChatAssistant, '_get_model_catalog', lambda self_: ()):
            self.assertEqual(Assistant._get_example_questions(), {})
