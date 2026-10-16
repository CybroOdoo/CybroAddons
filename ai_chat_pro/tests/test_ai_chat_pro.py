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
import wave
from datetime import date
from unittest.mock import patch

import requests

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_agent import AiChatAssistant as AiChatAgent
from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant, _keywords
from odoo.addons.ai_chat_pro.models.ai_chat_voice import DEFAULT_VOICE_MODEL, _VOICE_MODELS_CACHE, get_voice_models


def mock_decisions(**decisions):
    """ Patch the Decisions API to answer ``decisions``: an option for a choice,
    a boolean for a yes/no question. Return the calls made, and the patch. """
    calls = []

    def decide(self_, state, questions, usage, api_key=None, ai_model=None):
        calls.append((state, questions))
        usage['ai_called'] = True
        usage['prompt_tokens'] += 300
        usage['cost'] += 0.00001
        answers = {}
        for name, question in questions.items():
            value = decisions.get(name)
            if question['type'] == 'noul':
                answers[name] = {'type': 'noul', 'noul': 0.9 if value else 0.1}
            elif value is not None:
                answers[name] = {'type': 'choice', 'choice': value, 'confidence': 0.9}
        return answers
    return calls, patch.object(AiChatAssistant, '_decide', decide)


# the understanding of messages by Odoo's AI service, before the tests patch it
UNDERSTAND = AiChatAgent._understand


def mock_intent(intents=None, **default):
    """ Patch the understanding of messages by Odoo's AI service: ``intents`` maps a
    message to what the AI answers for it (``{'intent': 'create', 'target': ...}``),
    ``default`` is answered for the other messages, else the AI is unreachable. Return
    the messages understood, and the patch. """
    calls = []

    def understand(self_, question, usage, previous_plan=None, attachments=None):
        calls.append(question)
        answer = (intents or {}).get(question, default or None)
        written = f"{self_._describe_previous(previous_plan)}\n{self_._describe_memory()}".strip()
        return self_._clean_intent(answer, question, written, attachments)
    return calls, patch.object(AiChatAgent, '_understand', understand)


@tagged('post_install', '-at_install')
class TestAiChatPro(TransactionCase):

    # what the agent understands of the messages of these tests: Odoo's AI service is unreachable for the others
    INTENTS = {
        "list contacts named zeta sayuj": {'intent': 'query', 'names': [{'label': "name", 'text': "zeta sayuj"}]},
        "list contacts named zeta sayooj": {'intent': 'query', 'names': [{'label': "name", 'text': "zeta sayooj"}]},
        'pie chart of companies by number of "Zeta Partner" contacts': {'intent': 'query', 'chart': 'any'},
        'doughnut of companies by number of "Zeta Partner" contacts': {'intent': 'query', 'chart': 'doughnut'},
    }

    def setUp(self):
        super().setUp()
        self.understood, intent_mock = mock_intent(self.INTENTS)
        self.startPatcher(intent_mock)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env['ir.config_parameter'].sudo().set_str('ai_chat_pro.openrouter_api_key', 'test-key')
        cls.env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.use_olg', False)
        cls.company_a = cls.env['res.company'].create({'name': "Company A"})
        cls.company_b = cls.env['res.company'].create({'name': "Company B"})
        cls.user = new_test_user(
            cls.env, login='ai_chat_user', groups='base.group_user,ai_chat_pro.group_ai_chat_user',
            company_id=cls.company_a.id, company_ids=[cls.company_a.id],
        )
        cls.other_user = new_test_user(
            cls.env, login='ai_chat_other', groups='base.group_user,ai_chat_pro.group_ai_chat_user',
            company_id=cls.company_a.id, company_ids=[cls.company_a.id, cls.company_b.id],
        )
        cls.outsider = new_test_user(cls.env, login='ai_chat_outsider', groups='base.group_user')
        cls.partner_a = cls.env['res.partner'].create({'name': "Zeta Partner A", 'company_id': cls.company_a.id})
        cls.partner_b = cls.env['res.partner'].create({'name': "Zeta Partner B", 'company_id': cls.company_b.id})

    def _ask(self, user, question, conversation_id=False, candidates=None):
        """ Ask as a user, in all their companies, with the model detection pinned to
        a model of the base module. """
        if candidates is None:
            candidates = [{'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}]
        Conversation = self.env['ai.chat.conversation'].with_user(user).with_context(
            allowed_company_ids=user.company_ids.ids,
        )
        with patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: candidates):
            return Conversation.ask_question(conversation_id, question)

    def _rows(self, message):
        self.assertFalse(message['is_error'], message['content'])
        return [row['cells'] for row in message['result']['rows']]

    # ------------------------------------------------------------
    # Model detection
    # ------------------------------------------------------------

    def test_keywords(self):
        self.assertEqual(_keywords("List me the top 10 invoices"), {'invoice'})
        self.assertEqual(_keywords("which companies"), {'company'})

    def test_find_candidates_without_hard_coded_models(self):
        Assistant = self.env['ai.chat.assistant'].with_user(self.user)
        candidates = Assistant._find_candidates(_keywords("list the companies"))
        self.assertEqual(candidates[0]['model'], 'res.company')
        candidates = Assistant._find_candidates(_keywords("show me the currencies"))
        self.assertEqual(candidates[0]['model'], 'res.currency')
        models = {c['model'] for c in Assistant._find_candidates(_keywords("cache conversation parameter"))}
        self.assertFalse(models & {'ai.chat.conversation', 'ai.chat.message', 'ir.config_parameter'})

    def test_model_choice_by_ai(self):
        candidates = [
            {'model': 'res.partner', 'label': 'Contact', 'score': 4, 'path': 'Contacts', 'domain': ''},
            {'model': 'res.company', 'label': 'Companies', 'score': 3.5, 'path': 'Companies', 'domain': ''},
        ]
        Assistant = self.env['ai.chat.assistant'].with_user(self.user)
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False, 'cache': False}
        calls, mock = mock_decisions(data='option_1')
        with mock:
            # named by neither option: the AI chooses
            self.assertEqual(Assistant._choose_candidate("our organizations", candidates, usage)['model'], 'res.company')
            self.assertEqual(Assistant._choose_candidate("our organizations", candidates, usage)['model'], 'res.company')
        self.assertEqual(len(calls), 2, "never answered from a cache: the choice is asked again")

    # ------------------------------------------------------------
    # Decisions and queries
    # ------------------------------------------------------------

    def test_date_placeholders(self):
        Assistant = self.env['ai.chat.assistant'].with_context(tz='UTC')
        with patch('odoo.fields.Date.context_today', return_value=date(2026, 10, 8)):
            self.assertEqual(Assistant._resolve_value('$today'), date(2026, 10, 8))
            self.assertEqual(Assistant._resolve_value('$month_start'), date(2026, 10, 1))
            self.assertEqual(Assistant._resolve_value('$last_month_end'), date(2026, 9, 30))
            self.assertEqual(Assistant._resolve_value('$today-6d'), date(2026, 10, 2))
            self.assertEqual(Assistant._resolve_value('$quarter_start-1d'), date(2026, 9, 30))
            self.assertEqual(Assistant._resolve_value('$month_end+1m'), date(2026, 11, 30))
        field = self.env['res.partner']._fields['create_date']
        self.assertEqual(
            Assistant._make_leaf('create_date', '=', date(2026, 10, 8), field),
            ['&', ('create_date', '>=', '2026-10-08 00:00:00'), ('create_date', '<', '2026-10-09 00:00:00')],
        )

    def test_limit_extraction(self):
        # the count a question ranks is the one the agent read, never a pattern of words
        Assistant = self.env['ai.chat.assistant']
        self.assertFalse(Assistant._extract_limit("list me top 10 sale orders"), "nothing understood")
        for limit, expected in ((10, 10), ('5', 5), (0, False), (-3, False), (True, False), ("five", False),
                                (100000, 500)):
            intent = Assistant._clean_intent({'intent': 'query', 'limit': limit}, "a question")
            self.assertEqual(Assistant.with_context(ai_chat_intent=intent)._extract_limit("a question"), expected)

    def test_understanding_is_checked(self):
        Assistant = self.env['ai.chat.assistant']
        intent = Assistant._clean_intent({
            'intent': 'query', 'question': "  top 5   customers of  Azure  ", 'terms': ["customers", 7, None],
            'names': [{'label': "customer", 'text': "Azure"}, {'label': "product", 'text': "Invented Name"}],
            'chart': 'radar', 'follow_up': True, 'advice': 'yes',
        }, "top 5 customers of Azure")
        self.assertTrue(intent['routed'])
        self.assertEqual(intent['question'], "top 5 customers of Azure")
        self.assertEqual(intent['terms'], ["customers", "7"])
        self.assertEqual(intent['names'], [{'label': "customer", 'text': "Azure"}], "a name the message does not write")
        self.assertFalse(intent['chart'])
        self.assertFalse(intent['follow_up'], "no previous question to follow")
        self.assertFalse(intent['advice'])
        # what the AI can not answer: a question on the data
        for answer in (None, "text", {'intent': 'hack'}):
            self.assertEqual(Assistant._clean_intent(answer, "a question"), {'intent': 'query', 'routed': False})
        # a greeting without reply, a card without mention, an import without file: a question on the data
        for kind in ('chat', 'card', 'file'):
            self.assertEqual(Assistant._clean_intent({'intent': kind}, "hello")['intent'], 'query')
        self.assertEqual(Assistant._clean_intent({'intent': 'import'}, "import")['intent'], 'create')

    def test_understanding_is_never_cached(self):
        # each message is understood anew by Odoo's AI service: an earlier understanding could mislead
        prompts = []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            return 'Sure: {"intent":"query","question":"top 5 contacts","limit":5,"terms":["contacts"]}'
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False, 'cache': False}
        Assistant = self.env['ai.chat.assistant'].with_user(self.user)
        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            first = UNDERSTAND(Assistant, "Top 5 contacts", usage)
            again = UNDERSTAND(Assistant, "top 5  contacts", usage)
        self.assertEqual(len(prompts), 2)
        self.assertEqual(first, again)
        self.assertEqual((first['intent'], first['limit'], first['terms']), ('query', 5, ["contacts"]))
        self.assertIn("Message: Top 5 contacts", prompts[0])
        self.assertFalse(usage['ai_called'], "the decision model was not called")
        # Odoo's AI service unreachable: the message is read as a question on the data
        with patch.object(AiChatAssistant, '_olg_chat', lambda self_, prompt: (_ for _ in ()).throw(
                UserError("Odoo's AI service is unreachable."))):
            self.assertEqual(UNDERSTAND(Assistant, "other question", usage), {'intent': 'query', 'routed': False})

    def test_chat_answered_without_decision_model(self):
        _calls, mock = mock_decisions()
        _understood, intent_mock = mock_intent(intent='chat', reply="Hello! Ask me about your data.")
        with mock, intent_mock:
            message = self._ask(self.user, "hello")['messages'][1]
        self.assertEqual(message['content'], "Hello! Ask me about your data.")
        self.assertFalse(_calls, "a greeting costs no decision")
        self.assertFalse(message['decision_model'])

    def test_invalid_plans_are_rejected(self):
        Assistant = self.env['ai.chat.assistant'].with_user(self.user)
        with self.assertRaises(UserError):
            Assistant._prepare_query({'model': 'ir.config_parameter', 'mode': 'list'})
        query = Assistant._prepare_query({
            'model': 'res.partner', 'mode': 'list', 'filters': ['nope'], 'sort': 'password', 'limit': 9999,
            'menu_domain': "[('name', '=', 'x')]",
        })
        self.assertIsNone(query['order'])
        self.assertEqual(query['limit'], 50)
        self.assertEqual(list(query['domain']), [('name', '=', 'x')])

    def test_list_with_search_view_filter(self):
        archived = self.env['res.partner'].create({'name': "Zeta Partner C", 'active': False})
        calls, mock = mock_decisions(mode='list', sort='name', direction='asc', filter_inactive=True,
                                     names_record=True, name_field='name')
        with mock:
            message = self._ask(self.other_user, 'List the archived "Zeta Partner" contacts')['messages'][1]
        self.assertEqual([cells[0] for cells in self._rows(message)], [archived.name])
        state, questions = calls[0]
        filter_questions = [name for name in questions if name.startswith('filter_')]
        self.assertEqual(filter_questions[0], 'filter_inactive', "the filters the question mentions come first")
        self.assertGreater(len(filter_questions), 1, "the other filters are asked too")

    def test_named_record(self):
        # a name written in lower case is read; a name no record bears is said, with the names that come close
        self.env['res.partner'].create({'name': "Zeta Sayuj", 'company_id': self.company_a.id})
        _calls, mock = mock_decisions(mode='list', names_record=True, name_field='name')
        with mock:
            found = self._ask(self.user, "list contacts named zeta sayuj")['messages'][1]
            missing = self._ask(self.user, "list contacts named zeta sayooj")['messages'][1]
        self.assertEqual([cells[0] for cells in self._rows(found)], ["Zeta Sayuj"])
        self.assertIn('named "zeta sayooj"', missing['content'])
        self.assertIn("Did you mean Zeta Sayuj?", missing['content'])
        self.assertFalse(missing['result'], "no record is listed for a name that does not exist")
        self.assertEqual(missing['suggestions'], ["List contacts named Zeta Sayuj"])
        # the name is looked for on each question, not cached with the plan
        self.env['res.partner'].create({'name': "Zeta Sayooj", 'company_id': self.company_a.id})
        with mock:
            again = self._ask(self.user, "list contacts named zeta sayooj")['messages'][1]
        self.assertEqual([cells[0] for cells in self._rows(again)], ["Zeta Sayooj"])

    def test_answer_respects_record_rules(self):
        calls, mock = mock_decisions(mode='list', sort='name', direction='asc', names_record=True, name_field='name')
        with mock:
            message = self._ask(self.user, 'List the "Zeta Partner" contacts')['messages'][1]
        # the partner of the other company is filtered out by the multi-company record rule
        self.assertEqual([cells[0] for cells in self._rows(message)], ["Zeta Partner A"])
        self.assertEqual(message['tokens'], 300)

    def test_plan_never_cached(self):
        colleague = new_test_user(
            self.env, login='ai_chat_colleague', groups='base.group_user,ai_chat_pro.group_ai_chat_user',
            company_id=self.company_a.id, company_ids=[self.company_a.id],
        )
        calls, mock = mock_decisions(mode='count', names_record=True, name_field='name')
        with mock:
            first = self._ask(self.user, 'How many "Zeta Partner" contacts?')['messages'][1]
            second = self._ask(colleague, 'how many  "Zeta Partner" contacts')['messages'][1]
            # a user with other access sees other options, so gets their own decisions
            third = self._ask(self.other_user, 'how many "Zeta Partner" contacts')['messages'][1]
        self.assertEqual(len(calls), 3, "each question is decided anew, never answered from a cache")
        self.assertEqual({first['source'], second['source'], third['source']}, {'openrouter'})
        # each answer is computed with the access of the user asking
        self.assertEqual((first['result']['value'], second['result']['value'], third['result']['value']),
                         ('1', '1', '2'))

    def test_period_and_group(self):
        calls, mock = mock_decisions(mode='group', group_by='company_id', date_field='create_date', period='today',
                                     names_record=True, name_field='name')
        with mock:
            message = self._ask(self.other_user, '"Zeta Partner" contacts created today per company')['messages'][1]
        self.assertEqual(
            sorted((cells[0], cells[-1]) for cells in self._rows(message)),
            [("Company A", "1"), ("Company B", "1")],
        )

    def test_follow_up_question(self):
        calls, mock = mock_decisions(mode='list', names_record=True, name_field='name')
        with mock:
            first = self._ask(self.other_user, 'list "Zeta Partner" contacts')
            second = self._ask(self.other_user, 'only "Zeta Partner A"', first['conversation']['id'], candidates=[])
        self.assertIn("then:", calls[1][0])
        self.assertEqual([cells[0] for cells in self._rows(second['messages'][1])], ["Zeta Partner A"])

    # ------------------------------------------------------------
    # Security
    # ------------------------------------------------------------

    def test_conversations_are_private(self):
        calls, mock = mock_decisions(mode='count')
        with mock:
            answer = self._ask(self.user, "how many contacts")
        Conversation = self.env['ai.chat.conversation']
        self.assertEqual(
            Conversation.with_user(self.user).get_chat_data(answer['conversation']['id'])['conversation']['id'],
            answer['conversation']['id'],
        )
        self.assertFalse(Conversation.with_user(self.other_user).get_chat_data(answer['conversation']['id'])['conversation'])
        with self.assertRaises(AccessError):
            Conversation.with_user(self.other_user).ask_question(answer['conversation']['id'], "and now?")
        with self.assertRaises(AccessError):
            Conversation.with_user(self.outsider).get_chat_data()

    # ------------------------------------------------------------
    # Usage
    # ------------------------------------------------------------

    def test_usage(self):
        calls, mock = mock_decisions(mode='count')
        with mock:
            answer = self._ask(self.user, "how many contacts")
            other = self._ask(self.other_user, "how many contacts in all companies")
        self.assertEqual(answer['usage']['user'], {'tokens': 300, 'cost': 0.00001, 'questions': 1})
        self.assertFalse(answer['usage']['is_manager'])
        self.assertNotIn('balance', answer['usage'], "only administrators see the balance")

        manager = new_test_user(self.env, login='ai_chat_manager', groups='base.group_user,ai_chat_pro.group_ai_chat_manager')
        balance = {'amount': 4.5, 'kind': 'account', 'error': False}
        with patch.object(AiChatAssistant, '_get_openrouter_balance', lambda self_, refresh=False: balance):
            usage = self.env['ai.chat.conversation'].with_user(manager).get_usage()
        self.assertEqual(usage['user']['questions'], 0)
        self.assertEqual(usage['company']['questions'], 2)
        self.assertEqual(usage['company']['tokens'], 300 + other['messages'][1]['tokens'])
        self.assertEqual(usage['balance'], balance)

    def test_answer_names_the_decision_model(self):
        # the decision model (Jev) is named with the answers it chose the data of: each one, as none is cached
        self.env['ir.config_parameter'].sudo().set_str('ai_chat_pro.model', '~typesafe/jev-latest')
        _calls, mock = mock_decisions(mode='count')
        with mock:
            first = self._ask(self.user, "how many contacts are there")['messages'][1]
            again = self._ask(self.user, "how many contacts are there")['messages'][1]
        self.assertEqual((first['source'], first['decision_model']), ('openrouter', '~typesafe/jev-latest'))
        self.assertFalse(first['used_olg'])
        self.assertEqual((again['source'], again['decision_model']), ('openrouter', '~typesafe/jev-latest'))

    def test_openrouter_balance(self):
        class Response:
            def __init__(self, status, data):
                self.status_code, self.ok, self.data = status, status == 200, data

            def json(self):
                return self.data

            def raise_for_status(self):
                if not self.ok:
                    raise requests.HTTPError(self.status_code)

        Assistant = self.env['ai.chat.assistant']
        # a key without spending limit reads the balance of the account
        responses = [Response(200, {'data': {'limit': None, 'limit_remaining': None}}),
                     Response(200, {'data': {'total_credits': 10, 'total_usage': 2.5}})]
        with patch.object(requests, 'get', side_effect=responses):
            balance = Assistant._get_openrouter_balance(refresh=True)
        self.assertEqual((balance['amount'], balance['kind']), (7.5, 'account'))
        # a key with a limit reads what remains of it, not the balance of the account
        with patch.object(requests, 'get', return_value=Response(200, {'data': {'limit': 5, 'limit_remaining': 3.25}})):
            balance = Assistant._get_openrouter_balance(refresh=True)
        self.assertEqual((balance['amount'], balance['kind']), (3.25, 'key'))
        # the balance is kept a minute
        with patch.object(requests, 'get', side_effect=AssertionError("no call expected")):
            self.assertEqual(Assistant._get_openrouter_balance()['amount'], 3.25)

    # ------------------------------------------------------------
    # Totals from linking records
    # ------------------------------------------------------------

    def test_inbound_links_and_family(self):
        Assistant = self.env['ai.chat.assistant'].with_user(self.other_user)
        self.assertIn(('res.partner', 'company_id'), Assistant._get_inbound_links()['res.company'])
        # users are stored with their partner: linking to a user is linking to a contact
        self.assertIn('res.users', Assistant._get_model_family('res.partner'))

    def test_total_offered_to_the_ai(self):
        candidates = [{'model': 'res.company', 'label': 'Companies', 'score': 9, 'path': 'Companies', 'domain': ''}]
        total = {
            'model': 'res.partner', 'label': 'Contact', 'score': 2, 'signal': 2, 'path': 'Contacts', 'domain': '', 'context': '',
            'search_view_id': False, 'link_field': 'company_id', 'link_label': 'Company',
            'subject_label': 'Companies', 'measures': ['Credit Limit'],
        }
        Assistant = self.env['ai.chat.assistant'].with_user(self.other_user)
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False, 'cache': False}
        calls, mock = mock_decisions(data='option_1')
        with mock, patch.object(AiChatAssistant, '_get_total_candidates', lambda self_, c, k: [total]):
            chosen = Assistant._choose_candidate("companies with the most contacts", candidates, usage)
        self.assertEqual(chosen['link_field'], 'company_id', "a clear winner does not skip a matching total")
        options = calls[0][1]['data']['criteria']
        self.assertIn("Companies ranked or totaled from Contact", options['option_1'])
        self.assertIn("Companies [res.company] records themselves", options["option_0"])

    def test_records_named_in_full_are_listed(self):
        # "top contacts by ...": the contacts themselves, not the companies ranked by their contacts, nor tags
        contact = {'model': 'res.partner', 'label': 'Contact', 'score': 8, 'path': 'Contacts', 'domain': ''}
        company = {'model': 'res.company', 'label': 'Companies', 'score': 6.5, 'path': 'Companies', 'domain': ''}
        tag = {'model': 'res.partner.category', 'label': 'Contact Tag', 'score': 6.5, 'path': 'Contacts/Tags', 'domain': ''}
        Assistant = self.env['ai.chat.assistant'].with_user(self.other_user)
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False, 'cache': False}

        def decide(self_, *args, **kwargs):
            raise AssertionError("the records named in full are listed without asking the AI")
        with patch.object(AiChatAssistant, '_decide', decide):
            chosen = Assistant._choose_candidate("list me the newest contacts", [contact, company, tag], usage)
            self.assertEqual(chosen['model'], 'res.partner')
            chosen = Assistant._choose_candidate("list the contact tags", [tag, contact, company], usage)
            self.assertEqual(chosen['model'], 'res.partner.category')
        # another subject than the records asked for is not ranked when the question does not name it
        totals = Assistant._get_total_candidates([contact, company], _keywords("list me the newest contacts"))
        self.assertFalse([total for total in totals if total['subject_label'] == "Companies"])

    def test_total_from_linking_records(self):
        total = {
            'model': 'res.partner', 'label': 'Contact', 'score': 2, 'path': '', 'domain': '', 'context': '',
            'search_view_id': False, 'link_field': 'company_id', 'link_label': 'Company',
            'subject_label': 'Companies', 'measures': [],
        }
        calls, mock = mock_decisions(direction='desc', names_record=True, name_field='name')
        with mock, patch.object(AiChatAssistant, '_choose_candidate', lambda self_, *args, **kwargs: total):
            message = self._ask(self.other_user, 'companies by number of "Zeta Partner" contacts')['messages'][1]
            mine = self._ask(self.user, 'companies by number of "Zeta Partner" contacts')['messages'][1]
        result = message['result']
        self.assertNotIn('mode', calls[0][1], "the answer is one line per linked record, not asked")
        self.assertEqual((result['heading'], result['tags'][0]), ("Companies", "from Contact"))
        self.assertEqual(result['row_model'], 'res.company')
        self.assertEqual(
            sorted((row['id'], row['cells'][0], row['cells'][-1]) for row in result['rows']),
            sorted([(self.company_a.id, "Company A", "1"), (self.company_b.id, "Company B", "1")]),
        )
        # totals are computed with the access of the user asking: one company only
        self.assertEqual([cells[0] for cells in self._rows(mine)], ["Company A"])

    def test_least_ranked_linked_records(self):
        # "least selling products": the order of the ranking is asked, the lowest totals first
        self.env['res.partner'].create({'name': "Zeta Partner B2", 'company_id': self.company_b.id})
        total = {
            'model': 'res.partner', 'label': 'Contact', 'score': 2, 'path': '', 'domain': '', 'context': '',
            'search_view_id': False, 'link_field': 'company_id', 'link_label': 'Company',
            'subject_label': 'Companies', 'measures': [],
        }
        rankings = {}
        for direction in ('asc', 'desc'):
            calls, mock = mock_decisions(direction=direction, measure='none', names_record=True, name_field='name')
            with mock, patch.object(AiChatAssistant, '_choose_candidate', lambda self_, *args, **kwargs: total):
                message = self._ask(self.other_user, f'companies with the {direction} "Zeta Partner" contacts')
            self.assertIn('direction', calls[0][1], "the order of a ranking is asked")
            rankings[direction] = [cells[0] for cells in self._rows(message['messages'][1])]
        self.assertEqual(rankings['asc'], ["Company A", "Company B"])
        self.assertEqual(rankings['desc'], ["Company B", "Company A"])

    # ------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------

    COMPANY_TOTAL = {
        'model': 'res.partner', 'label': 'Contact', 'score': 2, 'path': '', 'domain': '', 'context': '',
        'search_view_id': False, 'link_field': 'company_id', 'link_label': 'Company',
        'subject_label': 'Companies', 'measures': [],
    }

    def _ask_total(self, question, **decisions):
        calls, mock = mock_decisions(direction='desc', names_record=True, name_field='name', **decisions)
        with mock, patch.object(AiChatAssistant, '_choose_candidate', lambda self_, *a, **k: self.COMPANY_TOTAL):
            message = self._ask(self.other_user, question)['messages'][1]
        return message, calls

    def test_chart_without_ai(self):
        def olg_chat(self_, prompt):
            raise AssertionError("no AI is needed for this chart")

        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            message, calls = self._ask_total('companies by number of "Zeta Partner" contacts')
        chart = message['result']['chart']
        self.assertEqual((chart['type'], chart['label'], chart['source'], chart['preferred']), ('bar', 0, 'local', True))
        count_index = len(message['result']['columns']) - 1
        self.assertEqual(chart['values'], [count_index])
        self.assertEqual(message['result']['rows'][0]['raw'][count_index], 1)

    def test_chart_by_period_is_a_line(self):
        calls, mock = mock_decisions(mode='group', group_by='create_date:date', granularity='day',
                                     names_record=True, name_field='name')
        self.env['res.partner'].create({'name': "Zeta Partner C", 'company_id': self.company_a.id})
        self.env.cr.execute(
            "UPDATE res_partner SET create_date = create_date - interval '3 days' WHERE name = 'Zeta Partner C'",
        )
        self.env['res.partner'].invalidate_model(['create_date'])
        with mock:
            message = self._ask(self.other_user, '"Zeta Partner" contacts created per day')['messages'][1]
        self.assertEqual(message['result']['chart']['type'], 'line')

    def test_chart_by_odoo_ai_only(self):
        prompts = []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            return 'Sure: {"type":"pie","label":0,"values":[1, 9]}'

        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            message, calls = self._ask_total('pie chart of companies by number of "Zeta Partner" contacts')
            again, again_calls = self._ask_total('pie chart of companies by number of "Zeta Partner" contacts')
        chart = message['result']['chart']
        self.assertEqual((chart['type'], chart['values'], chart['source']), ('pie', [1], 'odoo_ai'))
        self.assertEqual(len(prompts), 2, "the chart is chosen anew for each question")
        self.assertNotIn("Company A", prompts[0], "Odoo's AI chooses the chart from the columns, not the data")
        for _state, questions in calls + again_calls:
            self.assertFalse([name for name in questions if 'chart' in name], "OpenRouter is not asked about charts")

    def test_chart_type_read_by_the_agent(self):
        # the type of chart the agent read is drawn as is: Odoo's AI is not asked to choose it
        prompts = []
        with patch.object(AiChatAssistant, '_olg_chat', lambda self_, prompt: prompts.append(prompt) or "{}"):
            message, _calls = self._ask_total('doughnut of companies by number of "Zeta Partner" contacts')
        chart = message['result']['chart']
        self.assertEqual((chart['type'], chart['source'], chart['preferred']), ('doughnut', 'agent', True))
        self.assertFalse(prompts)

    def test_invalid_chart_from_ai_falls_back(self):
        with patch.object(AiChatAssistant, '_olg_chat', lambda self_, prompt: '{"type":"radar","label":7}'):
            message, _calls = self._ask_total('graph of companies by number of "Zeta Partner" contacts')
        self.assertEqual((message['result']['chart']['type'], message['result']['chart']['source']), ('bar', 'local'))

    # ------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------

    def test_export_xlsx(self):
        message, _calls = self._ask_total('companies by number of "Zeta Partner" contacts')
        record = self.env['ai.chat.message'].browse(message['id'])
        file_name, content = record.with_user(self.other_user)._export_xlsx()
        self.assertTrue(file_name.startswith("Companies_") and file_name.endswith(".xlsx"))
        openpyxl = __import__('openpyxl')
        sheet = openpyxl.load_workbook(io.BytesIO(content)).active
        self.assertEqual(sheet['A1'].value, "Companies")
        self.assertEqual(sheet['A2'].value, "from Contact, Zeta Partner")
        self.assertEqual([cell.value for cell in sheet[4]], ["Company", "Count"])
        values = sorted((row[0].value, row[1].value) for row in sheet.iter_rows(min_row=5))
        # numbers are numbers, to compute with them in the spreadsheet
        self.assertEqual(values, [("Company A", 1), ("Company B", 1)])
        with self.assertRaises(AccessError):
            record.with_user(self.user)._export_xlsx()

    # ------------------------------------------------------------
    # Model detection: menus of server actions, rare words, no data
    # ------------------------------------------------------------

    def test_menu_opening_a_server_action(self):
        """ Some menus open a server action returning a window action at run time: the
        code is never run, the model is the one declared on the server action, and the
        filters those of the window action named like the menu. """
        Assistant = self.env['ai.chat.assistant']
        window = self.env['ir.actions.act_window'].create({
            'name': "AI Outgoing Contacts", 'res_model': 'res.partner',
            'context': "{'search_default_supplier': 1}", 'domain': "[('active', '=', True)]",
        })
        server = self.env['ir.actions.server'].create({
            'name': "ai_chat_pro.method_contacts", 'model_id': self.env['ir.model']._get_id('res.partner'),
            'state': 'code', 'code': "raise UserError('never run')",
        })
        menu = self.env['ir.ui.menu'].create({'name': "AI Outgoing Contacts", 'action': f'ir.actions.server,{server.id}'})
        self.assertEqual(
            Assistant._get_menu_window_action(menu),
            ('res.partner', "AI Outgoing Contacts", "[('active', '=', True)]", "{'search_default_supplier': 1}",
             window.search_view_id.id),
        )
        menu.name = "AI Other Contacts"
        self.assertEqual(Assistant._get_menu_window_action(menu), ('res.partner', "AI Other Contacts", '', '', False))

    def test_rare_words_weigh_more(self):
        catalog = {entry[0]: entry for entry in self.env['ai.chat.assistant']._get_model_catalog()}
        weights = dict(catalog['res.currency'][2])
        # "res" names many models, "currency" few: both from the name of the model
        self.assertLess(weights['res'], 1.5)
        self.assertGreater(weights['currency'] / 2, weights['res'])

    def test_no_data_answers_the_question(self):
        candidates = [
            {'model': 'res.partner', 'label': 'Contact', 'score': 4, 'path': 'Contacts', 'domain': ''},
            {'model': 'res.company', 'label': 'Companies', 'score': 4, 'path': 'Companies', 'domain': ''},
        ]
        calls, mock = mock_decisions(data='none')
        with mock, patch.object(AiChatAssistant, '_get_total_candidates', lambda self_, *args: []):
            answer = self._ask(self.user, "late manufacturing orders", candidates=candidates)['messages'][1]
            again = self._ask(self.user, "late manufacturing orders", candidates=candidates)['messages'][1]
        self.assertIn("could not find any data", answer['content'])
        self.assertFalse(answer['result'])
        self.assertIn('none', calls[0][1]['data']['criteria'])
        self.assertEqual(len(calls), 2, "the answer that no data fits is decided anew too")
        self.assertIn("could not find any data", again['content'])

    # ------------------------------------------------------------
    # Voice questions
    # ------------------------------------------------------------

    def test_voice_questions(self):
        class Response:
            def __init__(self, status, data):
                self.status_code, self.ok, self.data, self.text = status, status == 200, data, str(data)

            def json(self):
                return self.data

            def raise_for_status(self):
                if not self.ok:
                    raise requests.HTTPError(self.status_code)

        def transcription(text, cost=0.0004):
            return Response(200, {
                'choices': [{'message': {'content': text}}],
                'usage': {'prompt_tokens': 160, 'completion_tokens': 8, 'cost': cost},
            })

        IrConfigParameter = self.env['ir.config_parameter'].sudo()
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        # half a second of 16 kHz mono PCM
        pcm = (b'\x00\x00' + (32767).to_bytes(2, 'little', signed=True)) * 4000
        audio = base64.b64encode(pcm).decode()

        self.assertFalse(Conversation.get_chat_data()['voice'], "voice questions are disabled by default")
        with self.assertRaises(UserError):
            Conversation.transcribe_audio(audio)
        IrConfigParameter.set_bool('ai_chat_pro.voice', True)
        IrConfigParameter.set_str('ai_chat_pro.openrouter_api_key', '')
        self.assertFalse(Conversation.get_chat_data()['voice'], "voice questions need the OpenRouter key")
        IrConfigParameter.set_str('ai_chat_pro.openrouter_api_key', 'test-key')
        self.assertTrue(Conversation.get_chat_data()['voice'])

        with patch.object(requests, 'post', return_value=transcription('"Invoices due today."')) as post:
            answer = Conversation.transcribe_audio(audio)
        self.assertEqual(answer['text'], "Invoices due today.", "the quotes a model may add are removed")
        payload = post.call_args.kwargs['json']
        self.assertEqual(post.call_args.args[0], 'https://openrouter.ai/api/v1/chat/completions')
        self.assertEqual(payload['model'], DEFAULT_VOICE_MODEL)
        sent = payload['messages'][0]['content'][1]['input_audio']
        self.assertEqual(sent['format'], 'wav')
        with wave.open(io.BytesIO(base64.b64decode(sent['data']))) as wav:
            self.assertEqual((wav.getframerate(), wav.getnchannels(), wav.getsampwidth()), (16000, 1, 2))
            self.assertEqual(wav.readframes(wav.getnframes()), pcm)
        self.assertEqual(answer['usage']['voice']['user'],
                         {'recordings': 1, 'seconds': 0.5, 'tokens': 168, 'cost': 0.0004})
        # answers are counted apart
        self.assertEqual(answer['usage']['user']['questions'], 0)

        # nobody speaks: no text, but the recording is paid for and counted
        with patch.object(requests, 'post', return_value=transcription("  ", cost=0.0001)):
            silence = Conversation.transcribe_audio(audio)
        self.assertEqual(silence['text'], "")
        self.assertEqual(silence['usage']['voice']['user']['recordings'], 2)
        self.assertAlmostEqual(silence['usage']['voice']['user']['cost'], 0.0005)

        # the model chosen in the settings; a Whisper model of a former version is replaced
        IrConfigParameter.set_str('ai_chat_pro.voice_model', 'mistralai/voxtral-small-24b-2507')
        with patch.object(requests, 'post', return_value=transcription("Hello")) as post:
            Conversation.transcribe_audio(audio)
        self.assertEqual(post.call_args.kwargs['json']['model'], 'mistralai/voxtral-small-24b-2507')
        IrConfigParameter.set_str('ai_chat_pro.voice_model', 'base')
        with patch.object(requests, 'post', return_value=transcription("Hello")) as post:
            Conversation.transcribe_audio(audio)
        self.assertEqual(post.call_args.kwargs['json']['model'], DEFAULT_VOICE_MODEL)

        with patch.object(requests, 'post', side_effect=AssertionError("no call expected")):
            with self.assertRaisesRegex(UserError, "could not be read"):
                Conversation.transcribe_audio("not base64!")
            with self.assertRaisesRegex(UserError, "Nothing was recorded"):
                Conversation.transcribe_audio(base64.b64encode(b'\x00').decode())
            with self.assertRaisesRegex(UserError, "too long"):
                Conversation.transcribe_audio(base64.b64encode(bytes(2 * 16000 * 121)).decode())
            with self.assertRaises(AccessError):
                self.env['ai.chat.conversation'].with_user(self.outsider).transcribe_audio(audio)

        # users see their own recordings, administrators all of them
        manager = new_test_user(self.env, login='ai_voice_manager', groups='base.group_user,ai_chat_pro.group_ai_chat_manager')
        with patch.object(AiChatAssistant, '_get_openrouter_balance', lambda self_, refresh=False: {}):
            manager_usage = self.env['ai.chat.conversation'].with_user(manager).get_usage()
        self.assertEqual(manager_usage['voice']['user']['recordings'], 0)
        self.assertEqual(manager_usage['voice']['company']['recordings'], 4)
        Transcription = self.env['ai.chat.transcription']
        self.assertEqual(Transcription.with_user(self.user).search_count([]), 4)
        self.assertEqual(Transcription.with_user(self.other_user).search_count([]), 0)

    def test_voice_models(self):
        class Response:
            ok = True

            def __init__(self, data):
                self.data = data

            def json(self):
                return {'data': self.data}

            def raise_for_status(self):
                pass

        def model(model_id, inputs, outputs, prompt, audio=None):
            return {
                'id': model_id, 'name': model_id.upper(),
                'architecture': {'input_modalities': inputs, 'output_modalities': outputs},
                'pricing': {'prompt': prompt, **({'audio': audio} if audio else {})},
            }

        _VOICE_MODELS_CACHE.clear()
        models = [
            model('a/text-only', ['text'], ['text'], '0.000001'),
            model('b/expensive', ['text', 'audio'], ['text'], '0.000002', '0.00003'),
            model('c/cheap', ['audio', 'text'], ['text'], '0.0000001', '0.0000003'),
            model('d/free', ['audio'], ['text'], '0'),
            model('e/router', ['audio'], ['text'], '-1'),
            model('f/speaks', ['audio'], ['audio'], '0.000001'),
            model('g/later:batch', ['audio'], ['text'], '0.00000001'),
            model('h/no-audio-price', ['audio'], ['text'], '0.000001'),
        ]
        with patch.object(requests, 'get', return_value=Response(models)):
            voice_models = get_voice_models()
        self.assertEqual([model_id for model_id, _label in voice_models],
                         ['d/free', 'c/cheap', 'h/no-audio-price', 'b/expensive'])
        labels = dict(voice_models)
        self.assertEqual(labels['d/free'], "D/FREE", "a free model says so in its name")
        self.assertIn("$0.30 / M audio tokens", labels['c/cheap'])
        self.assertIn("$1.00 / M input tokens", labels['h/no-audio-price'])
        # listed once an hour
        with patch.object(requests, 'get', side_effect=AssertionError("no call expected")):
            self.assertEqual(get_voice_models(), voice_models)
        # the settings always offer the model chosen
        self.env['ir.config_parameter'].sudo().set_str('ai_chat_pro.voice_model', 'z/chosen')
        selection = self.env['res.config.settings']._get_voice_model_selection()
        self.assertEqual(selection[0], ('z/chosen', 'z/chosen'))
        self.assertIn(DEFAULT_VOICE_MODEL, dict(selection))
        _VOICE_MODELS_CACHE.clear()

    def test_configuration_menu_for_administrators_only(self):
        configuration = self.env.ref('ai_chat_pro.ai_chat_menu_configuration')
        children = configuration.child_id
        ai_manager = new_test_user(self.env, login='ai_chat_ai_manager', groups='ai_chat_pro.group_ai_chat_manager')
        administrator = new_test_user(
            self.env, login='ai_chat_administrator', groups='ai_chat_pro.group_ai_chat_user,base.group_system',
        )
        for user in (self.user, ai_manager):
            visible = self.env['ir.ui.menu'].with_user(user)._visible_menu_ids()
            self.assertNotIn(configuration.id, visible, "only administrators configure the assistant")
            self.assertFalse(set(children.ids) & visible)
        visible = self.env['ir.ui.menu'].with_user(administrator)._visible_menu_ids()
        self.assertIn(configuration.id, visible)
        self.assertLessEqual(set(children.ids), visible)

    def test_data_matching_a_part_of_the_question(self):
        # "manufacturing orders" where only sales orders exist: the decision model may say no data answers it
        orders = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': '',
                  'unmatched': ['manufacturing']}
        calls, mock = mock_decisions(data='none')
        _understood, intent_mock = mock_intent(intent='query', terms=["manufacturing orders"])
        with mock, intent_mock:
            message = self._ask(self.user, "how many manufacturing orders are late", candidates=[orders])['messages'][1]
        self.assertIn("could not find any data", message['content'])
        self.assertIn('none', calls[0][1]['data']['criteria'])

    def test_follow_up_naming_other_data(self):
        # after contacts, "the companies of the second one" is about companies: no follow-up of the contacts
        contacts = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': '', 'domain': ''}
        companies = {'model': 'res.company', 'label': 'Companies', 'score': 9, 'path': '', 'domain': ''}
        _calls, mock = mock_decisions(mode='list')
        intents = {"list contacts": {'intent': 'query', 'terms': ["contacts"]},
                   "list the companies": {'intent': 'query', 'follow_up': True, 'terms': ["companies"]}}
        _understood, intent_mock = mock_intent(intents)
        with mock, intent_mock:
            first = self._ask(self.user, "list contacts", candidates=[contacts])
            again = self._ask(self.user, "list the companies", conversation_id=first['conversation']['id'],
                              candidates=[companies])['messages'][1]
        self.assertEqual(again['result']['model'], 'res.company')
