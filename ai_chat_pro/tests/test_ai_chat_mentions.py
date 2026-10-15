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

from unittest.mock import patch

from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_mentions import AiChatAssistant as AiChatMentions

from .test_ai_chat_creator import mock_values
from .test_ai_chat_pro import UNDERSTAND, mock_decisions, mock_intent

CONTACT = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': 'Contacts', 'domain': ''}


@tagged('post_install', '-at_install')
class TestAiChatMentions(TransactionCase):

    # what the agent understands of the messages of these tests
    INTENTS = {
        'show @Zeta Mention Co': {'intent': 'card'},
        'create a contact Mira Mention working at @Zeta Mention Co Ltd': {'intent': 'create', 'target': 'contact'},
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
            cls.env, login='ai_mention_user', groups='base.group_user,base.group_partner_manager,'
                                                     'ai_chat_pro.group_ai_chat_user',
        )
        cls.company = cls.env['res.partner'].create({
            'name': "Zeta Mention Co", 'is_company': True, 'email': "hello@zetamention.example.com", 'city': "Kochi",
        })
        # a partner of almost the same name: a name alone would match both
        cls.other = cls.env['res.partner'].create({'name': "Zeta Mention Co Ltd", 'is_company': True})
        cls.Conversation = cls.env['ai.chat.conversation'].with_user(cls.user)

    def _mention(self, record):
        return {'model': record._name, 'id': record.id}

    def test_search_mentions(self):
        with patch.object(AiChatMentions, '_get_mention_models', lambda self_: [('res.partner', "Contact")]):
            found = self.Conversation.search_mentions("Zeta Mention")
            self.assertEqual(self.Conversation.search_mentions("  "), [])
        self.assertEqual({(r['model'], r['id']) for r in found},
                         {('res.partner', self.company.id), ('res.partner', self.other.id)})
        self.assertEqual(found[0]['label'], "Contact")
        # records the user can not read, unknown models and deleted records are no mentions
        checked = self.Conversation._get_question_mentions([
            self._mention(self.company), {'model': 'no.such.model', 'id': 1}, {'model': 'res.partner', 'id': 0},
            {'model': 'ir.config_parameter', 'id': 1},
        ])
        self.assertEqual(checked, [{'model': 'res.partner', 'id': self.company.id, 'name': "Zeta Mention Co",
                                    'label': self.company._description}])

    def test_mention_filters_by_id(self):
        _calls, mock = mock_decisions(mode='list')
        with mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [CONTACT]):
            message = self.Conversation.ask_question(
                False, "list contacts of @Zeta Mention Co", False, None, [self._mention(self.company)])
        question, answer = self.Conversation.get_chat_data(False)['conversations'][0], message['messages'][1]
        self.assertEqual([row['id'] for row in answer['result']['rows']], [self.company.id],
                         "the very record mentioned, not the one of almost the same name")
        self.assertEqual(message['messages'][0]['mentions'][0]['id'], self.company.id)
        self.assertTrue(question)

    def test_record_card(self):
        message = self.Conversation.ask_question(
            False, "show @Zeta Mention Co", False, None, [self._mention(self.company)])['messages'][1]
        result = message['result']
        self.assertEqual((result['type'], result['model'], result['id']), ('record', 'res.partner', self.company.id))
        shown = {field['label']: field['value'] for field in result['fields']}
        self.assertEqual(shown.get('Email'), "hello@zetamention.example.com")

    def test_mention_in_a_record_to_create(self):
        _calls, mock = mock_values({'name': "Mira Mention", 'parent_id': "Zeta Mention Co"})
        with mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [CONTACT]):
            message = self.Conversation.ask_question(
                False, "create a contact Mira Mention working at @Zeta Mention Co Ltd", False, None,
                [self._mention(self.other)])['messages'][1]
        self.assertEqual(message['result']['values']['parent_id'], self.other.id,
                         "the company mentioned, not the one bearing the name the AI read")

    def test_typed_mention(self):
        # "@" typed without picking the record in the list: the record bearing that very name, the longest one
        # contacts are offered by "@" (the test database has no Contacts menu)
        self.startPatcher(patch.object(AiChatMentions, '_get_mention_models', lambda self_: [('res.partner', "Contact")]))
        message = self.Conversation.ask_question(False, "@Zeta Mention Co Ltd")
        self.assertEqual(message['messages'][0]['mentions'][0]['id'], self.other.id)
        answer = message['messages'][1]
        self.assertEqual((answer['result']['type'], answer['result']['id']), ('record', self.other.id),
                         "a record mentioned alone is shown without asking the AI")
        self.assertFalse(self.understood)
        self.assertEqual(self.env['ai.chat.conversation'].with_user(self.user)._find_typed_mentions(
            "orders of @Nobody Zeta Unknown"), [])

    def test_names_of_other_records_are_not_the_data_asked(self):
        # a reference of an order is no name of the products asked
        Assistant = self.env['ai.chat.assistant'].with_context(ai_chat_intent={'names': [
            {'label': "sales order", 'text': "S00006"}, {'label': "name", 'text': "Desk"},
        ]})
        self.assertEqual(Assistant._get_explicit_names("products of S00006", {'name': "Name"}, "Product"),
                         [('name', "Desk")])

    def test_records_linking_to_a_mentioned_record(self):
        # banks hold no contact: the bank accounts of the contact mentioned answer "banks of @contact"
        bank = self.env['res.bank'].create({'name': "Zeta Link Bank"})
        account = self.env['res.partner.bank'].create({
            'acc_number': "ZETA-0001", 'partner_id': self.company.id, 'bank_id': bank.id})
        self.env['res.bank'].create({'name': "Zeta Other Bank"})
        banks = {'model': 'res.bank', 'label': 'Bank', 'score': 9, 'path': '', 'domain': ''}
        _calls, mock = mock_decisions(mode='list')
        with mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [banks]):
            message = self.Conversation.ask_question(
                False, "list banks of @Zeta Mention Co", False, None, [self._mention(self.company)])['messages'][1]
        self.assertFalse(message['is_error'], message['content'])
        self.assertEqual(message['result']['model'], 'res.partner.bank')
        self.assertEqual([row['id'] for row in message['result']['rows']], [account.id])

    def test_record_named_without_mention(self):
        # the agent read a reference of another kind of record: it filters like a mention
        bank = self.env['res.bank'].create({'name': "Zeta Named Bank"})
        account = self.env['res.partner.bank'].create({
            'acc_number': "ZETA-0002", 'partner_id': self.other.id, 'bank_id': bank.id})
        banks = {'model': 'res.bank', 'label': 'Bank', 'score': 9, 'path': '', 'domain': ''}
        _calls, mock = mock_decisions(mode='list')
        _understood, intent_mock = mock_intent(intent='query', names=[{'label': "contact", 'text': "Zeta Mention Co Ltd"}])
        with mock, intent_mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [banks]), \
                patch.object(AiChatMentions, '_get_mention_models', lambda self_: [('res.partner', "Contact")]):
            message = self.Conversation.ask_question(False, "list banks of Zeta Mention Co Ltd")['messages'][1]
        self.assertFalse(message['is_error'], message['content'])
        self.assertEqual([row['id'] for row in message['result']['rows']], [account.id])

    # ------------------------------------------------------------
    # Memory of the conversation
    # ------------------------------------------------------------

    def _list_contacts(self):
        """ A conversation that listed the Zeta Mention contacts. """
        conversation = self.Conversation.create({'name': "Zeta contacts"})
        self.env['ai.chat.message'].create([{
            'conversation_id': conversation.id, 'role': 'user', 'content': "list the Zeta Mention contacts",
        }, {
            'conversation_id': conversation.id, 'role': 'assistant', 'content': "Contact: 2 record(s) found.",
            'plan': {'question': "list the Zeta Mention contacts", 'model': 'res.partner', 'menu_path': "Contacts"},
            'result': {'type': 'table', 'model': 'res.partner', 'openable': True, 'total': 2,
                       'columns': [{'label': "Name", 'numeric': False}],
                       'rows': [{'id': self.company.id, 'cells': ["Zeta Mention Co"]},
                                {'id': self.other.id, 'cells': ["Zeta Mention Co Ltd"]}]},
        }])
        return {'conversation': {'id': conversation.id}}

    def test_memory_of_the_conversation(self):
        first = self._list_contacts()
        conversation = self.env['ai.chat.conversation'].browse(first['conversation']['id'])
        memory = conversation.with_user(self.user)._get_memory()
        self.assertEqual([turn['role'] for turn in memory['turns']], ['user', 'assistant'])
        self.assertEqual(memory['turns'][0]['text'], "list the Zeta Mention contacts")
        self.assertIn("1. Zeta Mention Co", memory['turns'][1]['text'], "the records shown are remembered")
        self.assertEqual([(record['model'], record['id']) for record in memory['records']],
                         [('res.partner', self.company.id), ('res.partner', self.other.id)])
        # the next message is understood with the conversation so far
        prompts = []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            return '{"intent":"query","question":"list the banks of Zeta Mention Co Ltd",' \
                   '"names":[{"label":"contact","text":"Zeta Mention Co Ltd"}]}'
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False, 'cache': False}
        Assistant = self.env['ai.chat.assistant'].with_user(self.user).with_context(ai_chat_memory=memory)
        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            intent = UNDERSTAND(Assistant, "list the banks of the second one", usage)
        self.assertIn("Conversation so far:\nUser: list the Zeta Mention contacts", prompts[0])
        self.assertIn("Zeta Mention Co Ltd (Contact)", prompts[0])
        self.assertEqual(intent['question'], "list the banks of Zeta Mention Co Ltd")
        self.assertEqual(intent['names'], [{'label': "contact", 'text': "Zeta Mention Co Ltd"}],
                         "a name the conversation wrote, not the message")
        # another conversation remembers nothing of it
        self.assertEqual(self.Conversation.create({'name': "Other"})._get_memory(), {'turns': [], 'records': []})

    def test_records_of_the_conversation_are_exact_references(self):
        # "the second one": the very record the conversation showed, though "@" would not offer it
        first = self._list_contacts()
        bank = self.env['res.bank'].create({'name': "Zeta Memory Bank"})
        account = self.env['res.partner.bank'].create({
            'acc_number': "ZETA-0003", 'partner_id': self.other.id, 'bank_id': bank.id})
        banks = {'model': 'res.bank', 'label': 'Bank', 'score': 9, 'path': '', 'domain': ''}
        _calls, mock = mock_decisions(mode='list')
        _understood, intent_mock = mock_intent(intent='query', question="list the banks of Zeta Mention Co Ltd",
                                               names=[{'label': "contact", 'text': "Zeta Mention Co Ltd"}])
        with mock, intent_mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [banks]), \
                patch.object(AiChatMentions, '_get_mention_models', lambda self_: []):
            message = self.Conversation.ask_question(
                first['conversation']['id'], "list the banks of the second one")['messages'][1]
        self.assertFalse(message['is_error'], message['content'])
        self.assertEqual([row['id'] for row in message['result']['rows']], [account.id])

    def test_follow_up_naming_a_record_of_other_data(self):
        # "banks", then "banks of @contact": a follow-up of the banks, filtered through the bank accounts
        bank = self.env['res.bank'].create({'name': "Zeta Follow Bank"})
        account = self.env['res.partner.bank'].create({
            'acc_number': "ZETA-0004", 'partner_id': self.company.id, 'bank_id': bank.id})
        banks = {'model': 'res.bank', 'label': 'Bank', 'score': 9, 'path': '', 'domain': ''}
        _calls, mock = mock_decisions(mode='list')
        intents = {"list banks": {'intent': 'query'},
                   "list banks of @Zeta Mention Co": {'intent': 'query', 'follow_up': True}}
        _understood, intent_mock = mock_intent(intents)
        with mock, intent_mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [banks]):
            first = self.Conversation.ask_question(False, "list banks")
            message = self.Conversation.ask_question(
                first['conversation']['id'], "list banks of @Zeta Mention Co", False, None,
                [self._mention(self.company)])['messages'][1]
        self.assertEqual(message['result']['model'], 'res.partner.bank')
        self.assertEqual([row['id'] for row in message['result']['rows']], [account.id])

    def test_record_the_data_can_not_be_filtered_on(self):
        # tags hold nothing linking to banks: said, rather than all the banks listed
        tag = self.env['res.partner.category'].create({'name': "Zeta Unrelated Tag"})
        banks = {'model': 'res.bank', 'label': 'Bank', 'score': 9, 'path': '', 'domain': ''}
        _calls, mock = mock_decisions(mode='list')
        _understood, intent_mock = mock_intent(intent='query')
        with mock, intent_mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [banks]):
            message = self.Conversation.ask_question(
                False, "list banks of @Zeta Unrelated Tag", False, None, [self._mention(tag)])['messages'][1]
        self.assertFalse(message['result'])
        self.assertIn("could not find how Bank relate to", message['content'])
