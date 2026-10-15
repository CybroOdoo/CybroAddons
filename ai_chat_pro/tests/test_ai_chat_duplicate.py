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

from .test_ai_chat_creator import CONTACT, mock_values
from .test_ai_chat_pro import mock_intent


@tagged('post_install', '-at_install')
class TestAiChatDuplicate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_param('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_param('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_param('ai_chat_pro.allow_create', 'True')
        cls.user = new_test_user(
            cls.env, login='ai_duplicate_user', groups='base.group_user,base.group_partner_manager,'
                                                       'ai_chat_pro.group_ai_chat_user',
        )
        cls.tag = cls.env['res.partner.category'].create({'name': "Zeta Copy Tag"})
        cls.source = cls.env['res.partner'].create({
            'name': "Zeta Source Co", 'is_company': True, 'email': "source@example.com", 'phone': "+91 90000 11111",
            'city': "Kochi", 'category_id': [(6, 0, cls.tag.ids)],
        })
        cls.numbered = cls.env['res.partner'].create({'name': "ZS00100", 'email': "numbered@example.com"})

    def _ask(self, question, values=None, candidates=(CONTACT,), reference=None, target=None):
        """ Ask as a user, the agent understanding a request to duplicate ``reference``,
        else to create a ``target``. """
        _calls, mock = mock_values(values or {})
        _understood, intent_mock = mock_intent(intent='duplicate', reference=reference, target=target)
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        with mock, intent_mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: list(candidates)):
            return Conversation.ask_question(False, question)['messages'][1]

    def test_reference_texts(self):
        self.assertEqual(
            self.env['ai.chat.assistant']._get_reference_texts("sale order S00100"),
            ["S00100", "sale order S00100", "order S00100"],
        )

    def test_duplicate_with_changes(self):
        message = self._ask("duplicate the contact Zeta Source Co with email copy@example.com",
                            values={'email': "copy@example.com"}, reference="the contact Zeta Source Co")
        self.assertFalse(message['is_error'], message['content'])
        draft = message['result']
        self.assertEqual(draft['copy_of'], {'id': self.source.id, 'name': "Zeta Source Co"})
        shown = {field['label']: field['value'] for field in draft['fields']}
        self.assertEqual(shown['Copy of'], "Zeta Source Co")
        self.assertEqual(shown['Email'], "copy@example.com", "the change asked for")
        self.assertEqual(shown['Tags'], "Zeta Copy Tag", "a value copied")
        self.assertIn("copy", message['content'])

        partners = self.env['res.partner'].search_count([])
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        # the form of the copy is filled with the copied values and the changes
        context = Conversation.get_draft_form_action(message['id'])['context']
        self.assertEqual(context['default_email'], "copy@example.com")
        self.assertEqual(context['default_city'], "Kochi")
        created = Conversation.create_draft_record(message['id'])['result']
        copy = self.env['res.partner'].browse(created['res_id'])
        self.assertEqual(self.env['res.partner'].search_count([]), partners + 1)
        self.assertNotEqual(copy, self.source)
        self.assertEqual((copy.email, copy.city, copy.category_id), ("copy@example.com", "Kochi", self.tag))
        self.assertEqual(self.source.email, "source@example.com", "the record copied is unchanged")
        self.assertEqual(copy.create_uid, self.user, "copied as the user asking")

    def test_numbered_reference_in_any_model(self):
        # "duplicate ZS00100" names no kind of record: the numbered reference is looked for in the menus' models
        catalog = [('res.partner', "Contact", {}, [("Contacts", "", "", False, {})])]
        with patch.object(AiChatAssistant, '_get_model_catalog', lambda self_: catalog):
            message = self._ask("duplicate ZS00100", candidates=(), reference="ZS00100")
        self.assertFalse(message['is_error'], message['content'])
        self.assertEqual(message['result']['copy_of']['id'], self.numbered.id)

    def test_record_to_duplicate_not_found(self):
        with patch.object(AiChatAssistant, '_get_model_catalog', lambda self_: []):
            message = self._ask("duplicate ZZ99999", reference="ZZ99999")
        self.assertTrue(message['is_error'])
        self.assertIn("could not find the record \"ZZ99999\"", message['content'])

    def test_create_like_unknown_record_is_said(self):
        # "like" naming no record: said, rather than a record created that the user did not ask
        message = self._ask("create a contact like Nobody Known", values={'name': "Nobody Known"},
                            reference="Nobody Known", target="contact")
        self.assertTrue(message['is_error'])
        self.assertIn('could not find the record "Nobody Known"', message['content'])

    def test_copy_keeps_no_reference_of_the_record_copied(self):
        # the AI gives the name of the record copied as a change: the copy is no record of the same name
        message = self._ask("duplicate the contact Zeta Source Co", values={'name': "Zeta Source Co",
                                                                            'city': "Kochi"},
                            reference="Zeta Source Co")
        self.assertEqual(message['result']['values'], {}, "neither its name nor a value it holds already")

    def test_copy_of_a_record_mentioned_or_of_the_conversation(self):
        # "@" points to the very record, "the second one" to the record the conversation showed
        mention = [{'model': 'res.partner', 'id': self.numbered.id}]
        _calls, mock = mock_values({})
        _understood, intent_mock = mock_intent(intent='duplicate', reference="the second one")
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        with mock, intent_mock:
            message = Conversation.ask_question(False, "duplicate @ZS00100", False, None, mention)['messages'][1]
        self.assertEqual(message['result']['copy_of']['id'], self.numbered.id)
        memory = {'turns': [], 'records': [{'model': 'res.partner', 'id': self.source.id, 'name': "Zeta Source Co",
                                            'label': "Contact"}]}
        # no reference read: the record of the conversation the request, as the agent wrote it, names
        Assistant = self.env['ai.chat.assistant'].with_user(self.user).with_context(
            ai_chat_memory=memory, ai_chat_intent={'intent': 'duplicate', 'question': "duplicate Zeta Source Co"})
        self.assertEqual(Assistant._get_known_record_to_duplicate('')['record'], self.source)

    def test_numbered_record_never_named_by_the_request(self):
        if 'sale.order' not in self.env:
            self.skipTest("needs Sales")
        Assistant = self.env['ai.chat.assistant']
        self.assertTrue(Assistant._is_numbered(self.env['sale.order']), "orders are numbered by Odoo")
        self.assertFalse(Assistant._is_numbered(self.env['res.partner']))
        order = self.env['sale.order'].create({'partner_id': self.source.id})
        # "a sales order like S00042": a copy of that order
        found = Assistant.with_user(self.env.ref('base.user_admin'))._find_numbered_source(
            'sale.order', {'names': []}, f"create a sales order like {order.name} with 2 more chairs")
        self.assertEqual(found['record'], order)
