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

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_creator import (
    AiChatAssistant as AiChatCreator, _loads_loosely, _read_numbers,
)

from .test_ai_chat_pro import mock_decisions, mock_intent

CONTACT = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': 'Contacts', 'domain': ''}
COMPANY = {'model': 'res.company', 'label': 'Companies', 'score': 9, 'path': 'Companies', 'domain': ''}


def mock_values(values):
    """ Patch Odoo's AI service reading the values of a record to create, answering
    them in a code block as it may. Return the prompts it was given, and the patch. """
    calls = []

    def olg_chat(self_, prompt):
        calls.append(prompt)
        answer = values(prompt) if callable(values) else values
        return "```json\n" + json.dumps({'values': answer}) + "\n```"
    return calls, patch.object(AiChatAssistant, '_olg_chat', olg_chat)


@tagged('post_install', '-at_install')
class TestAiChatCreator(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        IrConfigParameter = cls.env['ir.config_parameter'].sudo()
        IrConfigParameter.set_str('ai_chat_pro.openrouter_api_key', 'test-key')
        IrConfigParameter.set_bool('ai_chat_pro.use_olg', False)
        IrConfigParameter.set_bool('ai_chat_pro.allow_create', True)
        cls.user = new_test_user(
            cls.env, login='ai_create_user', groups='base.group_user,base.group_partner_manager,'
                                                    'ai_chat_pro.group_ai_chat_user',
        )
        cls.other_user = new_test_user(
            cls.env, login='ai_create_other', groups='base.group_user,ai_chat_pro.group_ai_chat_user',
        )
        cls.company_partner = cls.env['res.partner'].create({'name': "Zeta Furniture", 'is_company': True})
        cls.tag = cls.env['res.partner.category'].create({'name': "Zeta VIP"})

    def _ask(self, question, candidates=(CONTACT,), user=None, intent=None, intents=None):
        """ Ask as a user, the agent understanding the message as a request to create a
        contact (or ``intent``), and the other messages it reads as ``intents`` say. """
        Conversation = self.env['ai.chat.conversation'].with_user(user or self.user)
        _understood, intent_mock = mock_intent(intents, **(intent or {'intent': 'create', 'target': 'contact'}))
        with intent_mock, patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: list(candidates)):
            return Conversation.ask_question(False, question)

    def test_create_fields(self):
        create_fields = self.env['ai.chat.assistant'].with_user(self.user)._get_create_fields(self.env['res.partner'])
        self.assertIn('name', create_fields)
        self.assertIn('email', create_fields)
        self.assertIn('parent_id', create_fields)
        self.assertIn('category_id', create_fields)
        # contacts of a company are lines of the form
        self.assertIn('email', create_fields['child_ids'])
        self.assertNotIn('parent_id', create_fields['child_ids'], "the line links to the record by itself")
        for name in ('id', 'display_name', 'create_date', 'image_1920', 'message_ids', 'active', 'company_id'):
            self.assertNotIn(name, create_fields)

    def test_draft_then_create(self):
        calls, mock = mock_values({
            'name': "John Smith", 'email': "john.smith@example.com", 'parent_id': "zeta furniture",
            'category_id': ["Zeta VIP"], 'type': "contact", 'unknown_field': "ignored",
            'child_ids': [{'name': "Jane Smith", 'email': "jane@example.com"}],
        })
        partners = self.env['res.partner'].search_count([])
        with mock:
            answer = self._ask("Create a new contact John Smith, john.smith@example.com, at Zeta Furniture, tag Zeta VIP, "
                                "with his colleague Jane Smith, jane@example.com")
        message = answer['messages'][1]
        draft = message['result']
        self.assertFalse(message['is_error'], message['content'])
        self.assertEqual((draft['type'], draft['state'], draft['model']), ('draft', 'draft', 'res.partner'))
        self.assertEqual(self.env['res.partner'].search_count([]), partners, "nothing is created before confirming")
        shown = {field['label']: field['value'] for field in draft['fields']}
        self.assertEqual(shown['Name'], "John Smith")
        self.assertEqual(shown['Email'], "john.smith@example.com")
        self.assertEqual(shown['Tags'], "Zeta VIP")
        self.assertIn("Zeta Furniture", shown['Related Company'])
        self.assertEqual(draft['lines'][0]['rows'], [["Jane Smith", "jane@example.com"]])
        self.assertFalse(draft['missing'])
        self.assertEqual(message['source'], 'olg', "Odoo's AI service read the values, without decision")
        # the AI is only given the fields of the record, and the request
        prompt = calls[0]
        self.assertIn("email (Email, text)", prompt)
        self.assertIn("child_ids (", prompt)
        self.assertNotIn("Zeta Furniture", prompt.replace(answer['messages'][0]['content'], ''))

        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        created = Conversation.create_draft_record(message['id'])
        self.assertEqual(created['result']['state'], 'created')
        partner = self.env['res.partner'].browse(created['result']['res_id'])
        self.assertEqual(partner.name, "John Smith")
        self.assertEqual(partner.email, "john.smith@example.com")
        self.assertEqual(partner.parent_id, self.company_partner)
        self.assertEqual(partner.category_id, self.tag)
        self.assertEqual(partner.child_ids.mapped('email'), ["jane@example.com"])
        self.assertEqual(partner.create_uid, self.user, "the record is created as the user asking")
        with self.assertRaisesRegex(UserError, "already created"):
            Conversation.create_draft_record(message['id'])

    def test_unknown_names_and_invalid_values(self):
        # users can not create countries: an unknown one is reported, not created
        _calls, mock = mock_values({'name': "Bob", 'country_id': "Atlantis", 'lang': "Klingon"})
        with mock:
            draft = self._ask("create a contact Bob in Atlantis, speaking Klingon")['messages'][1]['result']
        self.assertEqual(draft['type'], 'draft')
        self.assertEqual([field['label'] for field in draft['fields']], ['Name'])
        # the language is not one of the database: dropped as made up, before being checked
        self.assertEqual(len(draft['warnings']), 1)
        self.assertIn("Atlantis", draft['warnings'][0])
        self.assertNotIn('country_id', draft['values'])

    def test_missing_required_fields(self):
        _calls, mock = mock_values({'email': "nobody@example.com"})
        with mock, patch.object(AiChatCreator, '_get_missing_fields', lambda self_, Model, values: ['Name']):
            draft = self._ask("create a contact with email nobody@example.com")['messages'][1]['result']
        self.assertEqual(draft['missing'], ['Name'])

    def test_discard_and_form(self):
        _calls, mock = mock_values({'name': "Draft Person", 'email': "draft@example.com"})
        with mock:
            message = self._ask("create a contact Draft Person, draft@example.com")['messages'][1]
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        action = Conversation.get_draft_form_action(message['id'])
        self.assertEqual(action['res_model'], 'res.partner')
        self.assertEqual(action['context'], {'default_name': "Draft Person", 'default_email': "draft@example.com"})
        with self.assertRaises(AccessError):
            self.env['ai.chat.conversation'].with_user(self.other_user).create_draft_record(message['id'])
        discarded = Conversation.discard_draft(message['id'])
        self.assertEqual(discarded['result']['state'], 'discarded')
        with self.assertRaisesRegex(UserError, "already created or discarded"):
            Conversation.create_draft_record(message['id'])
        self.assertFalse(self.env['res.partner'].search_count([('email', '=', "draft@example.com")]))

    def test_only_models_the_user_can_create(self):
        # internal users can not create companies: said, rather than creating something else
        calls, mock = mock_decisions(mode='count')
        _value_calls, values_mock = mock_values({'name': "Evil Corp"})
        with mock, values_mock:
            message = self._ask("create a company Evil Corp", candidates=[COMPANY],
                                intent={'intent': 'create', 'target': 'company'})['messages'][1]
        self.assertNotEqual((message['result'] or {}).get('type'), 'draft')
        self.assertFalse([prompt for prompt in _value_calls if "You fill in a new record" in prompt])
        self.assertIn("I can not create a company", message['content'])

    def test_ambiguous_verb_understood_by_the_agent(self):
        # "add" may ask to change an answer: the agent's understanding of the message decides, no pattern
        calls, mock = mock_decisions(mode='list')
        value_calls, values_mock = mock_values({'name': "Amount"})
        with mock, values_mock:
            message = self._ask("add the contacts column", intent={'intent': 'query'})['messages'][1]
        self.assertNotEqual((message['result'] or {}).get('type'), 'draft')
        self.assertFalse([prompt for prompt in value_calls if "You fill in a new record" in prompt])

        with values_mock:
            message = self._ask("add contact Paul Martin")['messages'][1]
        self.assertEqual(message['result']['type'], 'draft')

    def test_creation_disabled(self):
        self.env['ir.config_parameter'].sudo().set_bool('ai_chat_pro.allow_create', False)
        calls, mock = mock_decisions(mode='count')
        value_calls, values_mock = mock_values({'name': "Nobody"})
        with mock, values_mock:
            message = self._ask("create a contact Nobody")['messages'][1]
        self.assertNotEqual((message['result'] or {}).get('type'), 'draft')
        self.assertFalse(value_calls)

    def test_odoo_ai_unavailable(self):
        def olg_chat(self_, prompt):
            raise UserError("You do not have enough credits to use Odoo's AI service.")

        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            message = self._ask("create a contact Nobody")['messages'][1]
        self.assertTrue(message['is_error'])
        self.assertIn("enough credits", message['content'])

    def test_loose_json(self):
        self.assertEqual(_loads_loosely('Here: ```json\n{"values": {"name": "A"}}\n```'), {'values': {'name': "A"}})
        # a stray closing bracket, as Odoo's AI service may write
        self.assertEqual(
            _loads_loosely('{"values":{"child_ids":[{"name":"Ana"},{"name":"Luis"}}]}}'),
            {'values': {'child_ids': [{'name': "Ana"}, {'name': "Luis"}]}},
        )
        # brackets in strings are text, and missing closing brackets are added
        self.assertEqual(_loads_loosely('{"values":{"name":"A } ] B"'), {'values': {'name': "A } ] B"}})
        self.assertIsNone(_loads_loosely("no JSON here"))

    def test_empty_draft_is_not_created(self):
        _calls, mock = mock_values({})
        with mock:
            message = self._ask("create a contact")['messages'][1]
        self.assertFalse(message['result']['fields'])
        with self.assertRaisesRegex(UserError, "no value"):
            self.env['ai.chat.conversation'].with_user(self.user).create_draft_record(message['id'])

    def _mock_query(self, result):
        """ Patch the data tool answering the description of records, as a question.
        Return the descriptions asked, with the number of records asked first. """
        asked = []

        def answer_data(self_, question, previous_plan, usage):
            limit = self_._get_intent().get('limit')
            asked.append(f"{limit} {question}" if limit else question)
            return {'content': '', 'result': result}
        return asked, patch.object(AiChatAssistant, '_answer_data', answer_data)

    def test_lines_described_by_a_query(self):
        countries = self.env['res.country'].search([], limit=3)
        asked, query_mock = self._mock_query({
            'type': 'table', 'model': 'res.country', 'rows': [{'id': country.id} for country in countries],
        })
        _calls, mock = mock_values({
            'name': "Export Co",
            # delivery addresses keep their own country, contacts take the one of their company
            'child_ids': [{'name': "Branch", 'type': 'delivery', 'country_id': {'$query': "our 3 main countries"}}],
        })
        with mock, query_mock:
            draft = self._ask("create a contact Export Co with a Branch delivery address in our 3 main countries")[
                'messages'][1]['result']
        self.assertEqual(asked, ["our 3 main countries"])
        self.assertEqual(len(draft['lines'][0]['rows']), 3, "one line per record found")
        self.assertEqual([row[-1] for row in draft['lines'][0]['rows']], countries.mapped('display_name'))
        self.assertIn("our 3 main countries", draft['notes'][0])
        message_id = self.env['ai.chat.message'].search([], order='id desc', limit=1).id
        partner = self.env['res.partner'].browse(
            self.env['ai.chat.conversation'].with_user(self.user).create_draft_record(message_id)['result']['res_id']
        )
        self.assertEqual(partner.child_ids.country_id, countries)

    def _mock_count_question(self, values, count):
        """ Patch the AI reading the values of a record to create, and the number of
        records a description counts in the request. Return the count questions. """
        questions = []

        def olg_chat(self_, prompt):
            if "how many records" in prompt:
                questions.append(prompt)
                return json.dumps({'count': count})
            return json.dumps({'values': values})
        return questions, patch.object(AiChatAssistant, '_olg_chat', olg_chat)

    def test_count_given_with_a_query(self):
        # "our most selling 5 products": the AI gives the description and its count apart
        countries = self.env['res.country'].search([], limit=10)
        asked, query_mock = self._mock_query({
            'type': 'table', 'model': 'res.country', 'rows': [{'id': country.id} for country in countries],
        })
        questions, mock = self._mock_count_question({
            'name': "Most Co",
            'child_ids': [{'name': "Branch", 'type': 'delivery',
                           'country_id': {'$query': "most visited countries", '$count': 5}}],
        }, None)
        with mock, query_mock:
            draft = self._ask(
                "create a contact Most Co with a Branch delivery address in our most visited 5 countries"
            )['messages'][1]['result']
        self.assertEqual(asked, ["5 most visited countries"])
        self.assertEqual([row[-1] for row in draft['lines'][0]['rows']], countries[:5].mapped('display_name'))
        self.assertFalse(questions, "the count given, it is not asked again")

    def test_count_left_out_of_a_query(self):
        # the AI drops the count the request gives, before or after the description: it is asked
        # to read it in the request, and the lines are as many as asked
        countries = self.env['res.country'].search([], limit=10)
        for request, count in (
            ("create a contact Few Co with a Branch delivery address in 2 of our least visited countries", 2),
            ("create a contact Few Co with Branch delivery addresses in our least visited countries. "
             "Three countries, one branch each", 3),
        ):
            asked, query_mock = self._mock_query({
                'type': 'table', 'model': 'res.country', 'rows': [{'id': country.id} for country in countries],
            })
            questions, mock = self._mock_count_question({
                'name': "Few Co",
                'child_ids': [{'name': "Branch", 'type': 'delivery',
                               'country_id': {'$query': "our least visited countries"}}],
            }, count)
            with mock, query_mock:
                draft = self._ask(request)['messages'][1]['result']
            self.assertEqual(asked, [f"{count} our least visited countries"], "the count is asked with the description")
            self.assertEqual([row[-1] for row in draft['lines'][0]['rows']], countries[:count].mapped('display_name'))
            self.assertIn(request, questions[0])

    def test_read_numbers(self):
        # amounts of documents keep their thousands separators
        numbers = _read_numbers("20 x 1,450.00 = 29,000.00; 1,23,456.50; 1.450,75; 3,5 kg; 2 laptops")
        for number in (20, 1450, 29000, 123456.5, 1450.75, 3.5, 2):
            self.assertIn(number, numbers)

    def test_single_record_described(self):
        # a field holding one record ("my best salesperson"): no number of records is asked
        salesman = new_test_user(self.env, login='ai_create_single', groups='base.group_user')
        asked, query_mock = self._mock_query({
            'type': 'table', 'model': 'res.users', 'rows': [{'id': salesman.id}],
        })
        questions, mock = self._mock_count_question(
            {'name': "Single Co", 'user_id': {'$query': "my best salesperson"}}, 1)
        with mock, query_mock:
            draft = self._ask("create a contact Single Co for my best salesperson")['messages'][1]['result']
        self.assertEqual(asked, ["my best salesperson"])
        self.assertEqual(draft['values']['user_id'], salesman.id)
        self.assertFalse(questions)

    def test_no_count_in_the_request(self):
        # no number of records in the request: all those the description finds
        countries = self.env['res.country'].search([], limit=4)
        asked, query_mock = self._mock_query({
            'type': 'table', 'model': 'res.country', 'rows': [{'id': country.id} for country in countries],
        })
        questions, mock = self._mock_count_question({
            'name': "All Co",
            'child_ids': [{'name': "Branch", 'type': 'delivery', 'country_id': {'$query': "our new countries"}}],
        }, None)
        with mock, query_mock:
            draft = self._ask("create a contact All Co with a Branch delivery address in our new countries")[
                'messages'][1]['result']
        self.assertEqual(asked, ["our new countries"])
        self.assertEqual(len(draft['lines'][0]['rows']), 4)
        self.assertEqual(len(questions), 1)

    def test_query_repeated_on_lines(self):
        # the AI gives a description once per record it counts: these records are found once
        countries = self.env['res.country'].search([], limit=10)
        asked, query_mock = self._mock_query({
            'type': 'table', 'model': 'res.country', 'rows': [{'id': country.id} for country in countries],
        })
        line = {'name': "Branch", 'type': 'delivery', 'country_id': {'$query': "our least visited countries"}}
        _calls, mock = mock_values({'name': "Repeat Co", 'child_ids': [line] * 4})
        with mock, query_mock:
            draft = self._ask(
                "create a contact Repeat Co with Branch delivery addresses in our least visited countries"
            )['messages'][1]['result']
        self.assertEqual(asked, ["4 our least visited countries"], "the description is asked once, with its count")
        self.assertEqual([row[-1] for row in draft['lines'][0]['rows']], countries[:4].mapped('display_name'))
        self.assertEqual(len(draft['notes']), 1)

    def test_query_results_of_a_parent_model(self):
        # a query listing contacts, for a field linking to users: the users of these contacts
        salesman = new_test_user(self.env, login='ai_create_salesman', groups='base.group_user')
        _asked, query_mock = self._mock_query({
            'type': 'table', 'row_model': 'res.partner', 'model': 'sale.report',
            'rows': [{'id': salesman.partner_id.id}],
        })
        _calls, mock = mock_values({'name': "Lead Contact", 'user_id': {'$query': "my best salesperson"}})
        with mock, query_mock:
            draft = self._ask("create a contact Lead Contact for my best salesperson")['messages'][1]['result']
        self.assertEqual(draft['values']['user_id'], salesman.id)

    def test_lines_with_unknown_records_are_left_out(self):
        _calls, mock = mock_values({
            'name': "Lines Co",
            'child_ids': [
                {'name': "Kept", 'country_id': "Belgium"},
                {'name': "Left out", 'country_id': "top selling country 1"},
            ],
        })
        with mock:
            draft = self._ask("create a contact Lines Co with Kept in Belgium and Left out in top selling country 1")['messages'][1]['result']
        self.assertEqual([row[0] for row in draft['lines'][0]['rows']], ["Kept"])
        self.assertTrue(any("left out" in warning for warning in draft['warnings']))

    def test_query_finding_nothing(self):
        _asked, query_mock = self._mock_query({'type': 'value', 'value': 0, 'model': 'res.country'})
        _calls, mock = mock_values({'name': "Nowhere Co", 'country_id': {'$query': "our favourite country"}})
        with mock, query_mock:
            draft = self._ask("create a contact Nowhere Co in our favourite country")['messages'][1]['result']
        self.assertNotIn('country_id', draft['values'])
        self.assertIn("our favourite country", draft['warnings'][0])

    # ------------------------------------------------------------
    # Plans: records the request needs, created first
    # ------------------------------------------------------------

    def test_plan_for_a_new_company(self):
        def values(prompt):
            if 'Only the Contact "Nova Industries"' in prompt:
                return {'name': "Nova Industries", 'email': "hello@nova.example.com"}
            return {'name': "Bob Stone", 'email': "bob@nova.example.com", 'parent_id': "Nova Industries"}

        calls, mock = mock_values(values)
        with mock:
            message = self._ask("create a contact Bob Stone, bob@nova.example.com, at the new company "
                                "Nova Industries, hello@nova.example.com")['messages'][1]
        plan = message['result']
        self.assertEqual((plan['type'], plan['state'], plan['current']), ('plan', 'draft', 0))
        self.assertEqual(len(calls), 2, "the values of the new company are read from the request too")
        company_step, contact_step = plan['steps']
        self.assertEqual(company_step['model'], 'res.partner')
        self.assertIn("Nova Industries", company_step['title'])
        self.assertIn({'label': "Email", 'value': "hello@nova.example.com"}, company_step['fields'])
        self.assertEqual(contact_step['values']['parent_id'], {'$step': 0})
        self.assertIn("Nova Industries (new)", [field['value'] for field in contact_step['fields']])
        self.assertFalse(contact_step['missing'])
        self.assertFalse(self.env['res.partner'].search_count([('name', '=', "Nova Industries")]))

        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        # the form of the first step is filled with its values
        self.assertEqual(Conversation.get_draft_form_action(message['id'])['context']['default_name'],
                         "Nova Industries")
        first = Conversation.create_draft_record(message['id'])['result']
        self.assertEqual((first['state'], first['current']), ('draft', 1))
        company = self.env['res.partner'].browse(first['steps'][0]['res_id'])
        self.assertEqual(company.email, "hello@nova.example.com")
        self.assertIn(company.display_name, [field['value'] for field in first['steps'][1]['fields']])
        # the form of the next step links to the record created
        self.assertEqual(Conversation.get_draft_form_action(message['id'])['context']['default_parent_id'],
                         company.id)

        last = Conversation.create_draft_record(message['id'])['result']
        self.assertEqual(last['state'], 'created')
        contact = self.env['res.partner'].browse(last['res_id'])
        self.assertEqual((contact.name, contact.parent_id), ("Bob Stone", company))
        with self.assertRaisesRegex(UserError, "already created"):
            Conversation.create_draft_record(message['id'])

    def test_plan_new_tag_marked_by_the_ai(self):
        # a name marked as new, by the AI and by the agent, is created even if a record bears a close name
        premium = self.env['res.partner.category'].create({'name': "Premium Partners"})
        _calls, mock = mock_values({'name': "Tagged Person", 'category_id': [{'$new': "Premium"}, "Zeta VIP"]})
        request = "create a contact Tagged Person with the new tag Premium and Zeta VIP"
        with mock:
            # the agent did not read it as new: the record bearing that name is linked
            draft = self._ask(request)['messages'][1]['result']
            self.assertEqual(draft['values']['category_id'], [[6, 0, [premium.id, self.tag.id]]])
            plan = self._ask(request, intent={'intent': 'create', 'target': 'contact', 'names': [
                {'label': "tag", 'text': "Premium", 'new': True}]})['messages'][1]['result']
        self.assertEqual(plan['type'], 'plan')
        self.assertEqual(plan['steps'][0]['model'], 'res.partner.category')
        self.assertEqual(plan['steps'][1]['values']['category_id'], [[6, 0, [{'$step': 0}, self.tag.id]]])
        message_id = self.env['ai.chat.message'].search([], order='id desc', limit=1).id
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        Conversation.create_draft_record(message_id)
        partner = self.env['res.partner'].browse(Conversation.create_draft_record(message_id)['result']['res_id'])
        self.assertEqual(sorted(partner.category_id.mapped('name')), ["Premium", "Zeta VIP"])

    def test_plan_same_new_record_once(self):
        _calls, mock = mock_values({
            'name': "Twice Co",
            'parent_id': "Ghost Ltd",
            'category_id': [{'$new': "Ghost Tag"}, {'$new': "ghost tag"}],
        })
        with mock:
            plan = self._ask("create a contact Twice Co at Ghost Ltd, with the new tag Ghost Tag")['messages'][1]['result']
        self.assertEqual([step['model'] for step in plan['steps']],
                         ['res.partner', 'res.partner.category', 'res.partner'],
                         "a new record named twice is created once")

    def test_plan_discard_the_rest(self):
        def values(prompt):
            if 'Only the Contact' in prompt:
                return {}
            return {'name': "Kept Apart", 'parent_id': "Lonely Corp"}

        _calls, mock = mock_values(values)
        with mock:
            message = self._ask("create a contact Kept Apart at Lonely Corp")['messages'][1]
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        Conversation.create_draft_record(message['id'])
        result = Conversation.discard_draft(message['id'])['result']
        self.assertEqual(result['state'], 'discarded')
        self.assertEqual([step['state'] for step in result['steps']], ['created', 'discarded'])
        self.assertTrue(self.env['res.partner'].search_count([('name', '=', "Lonely Corp")]),
                        "the records already created are kept")
        self.assertFalse(self.env['res.partner'].search_count([('name', '=', "Kept Apart")]))

    def test_values_not_in_the_request_are_ignored(self):
        _calls, mock = mock_values({
            'name': "Grounded Person", 'email': "made.up@example.com", 'lang': "fr_FR",
            'category_id': ["Zeta VIP"], 'child_ids': [{'name': "Invented Child", 'email': "kid@example.com"}],
        })
        with mock:
            draft = self._ask("create a contact Grounded Person")['messages'][1]['result']
        self.assertEqual(draft['values'], {'name': "Grounded Person"})
        self.assertFalse(draft['lines'])

    def test_dates_must_be_the_ones_of_the_request(self):
        Assistant = self.env['ai.chat.assistant']
        # the date of a currency rate: a date field to fill
        Rate = self.env['res.currency.rate']
        cases = [
            # a date written in full: only that date is kept, not a date made up next to it
            ("rate of 2026-10-20", "2026-10-09", None, False),
            ("rate of 2026-10-20", "2026-10-20", None, True),
            # a date in words, in any language, is computed by the AI, that quotes the words it read it from
            ("rate of yesterday", "2026-10-08", "yesterday", True),
            ("taux d'hier", "2026-10-08", "hier", True),
            ("rate of yesterday", "2026-10-08", None, False),
            # words the request does not write, or a whole sentence of it: the date is made up
            ("rate for 2 currencies", "2026-10-09", "today", False),
            ("rate for 2 currencies, please do it now", "2026-10-09", "rate for 2 currencies, please do it", False),
            # a word of the request the agent did not read as a date
            ("rate of the euro, then the dollar", "2026-10-09", "then", False),
        ]
        for request, date, words, kept in cases:
            values = {'name': date, '$from': {'name': words}} if words else {'name': date}
            # the words the agent read as dates in the request
            spoken = [word for word in ("yesterday", "hier") if word in request]
            grounded = Assistant.with_context(ai_chat_intent={'spoken': spoken})._keep_grounded_values(
                request, Rate, {'name': None}, values)
            self.assertEqual('name' in grounded, kept, f"{request!r}: {date} from {words!r}")
        # numbers in words, in any language: by the words quoted
        Line = self.env['res.partner']
        grounded = Assistant.with_context(ai_chat_intent={'spoken': ["deux"]})._keep_grounded_values(
            "un contact avec deux couleurs", Line, {'color': None}, {'color': 2, '$from': {'color': "deux"}})
        self.assertEqual(grounded, {'color': 2})
        # a number quoted in figures is the very one
        grounded = Assistant._keep_grounded_values(
            "a contact with 3 colours", Line, {'color': None}, {'color': 5, '$from': {'color': "3 colours"}})
        self.assertEqual(grounded, {})

    def test_described_record_given_by_its_name(self):
        # the AI may describe a record by its very name: it is found without asking a question
        asked, query_mock = self._mock_query({'type': 'value', 'value': 0})
        _calls, mock = mock_values({'name': "Named Co", 'category_id': {'$query': "Zeta VIP"}})
        with mock, query_mock:
            draft = self._ask("create a contact Named Co with tag Zeta VIP")['messages'][1]['result']
        self.assertFalse(asked)
        self.assertEqual(draft['values']['category_id'], [[6, 0, [self.tag.id]]])

    def test_new_record_of_a_plan_has_no_lines(self):
        def values(prompt):
            if 'Only the Contact "Fresh Corp"' in prompt:
                # the AI puts in the new company a part of the request meant for the contact
                return {'name': "Fresh Corp", 'child_ids': [{'name': "Fresh Child"}]}
            return {'name': "Fresh Child", 'parent_id': "Fresh Corp"}

        calls, mock = mock_values(values)
        with mock:
            plan = self._ask("create a contact Fresh Child at the new company Fresh Corp")['messages'][1]['result']
        self.assertNotIn("child_ids (", calls[1], "lines are not offered for a record created along the way")
        self.assertFalse(plan['steps'][0]['lines'])

    def test_own_name_is_no_link(self):
        # the AI gives the name of the record to create as a record it links to: no new one is planned for it
        _calls, mock = mock_values({'name': "Selfie Corp", 'parent_id': "Selfie Corp"})
        with mock:
            draft = self._ask("create a contact called Selfie Corp")['messages'][1]['result']
        self.assertEqual(draft['type'], 'draft')
        self.assertEqual(draft['values'], {'name': "Selfie Corp"})

    def test_described_records_are_counted(self):
        # the query answers more records than the description counts: only that many are kept
        countries = self.env['res.country'].search([], limit=7)
        _asked, query_mock = self._mock_query({
            'type': 'table', 'model': 'res.country', 'rows': [{'id': country.id} for country in countries],
        })
        _calls, mock = mock_values({
            'name': "Counted Co",
            'child_ids': [{'name': "Depot", 'type': 'delivery', 'country_id': {'$query': "our top five countries"}}],
        })
        with mock, query_mock:
            draft = self._ask("create a contact Counted Co with a Depot delivery address in our top five countries",
                              intents={"our top five countries": {'intent': 'query', 'limit': 5}})[
                'messages'][1]['result']
        self.assertEqual([row[-1] for row in draft['lines'][0]['rows']], countries[:5].mapped('display_name'))

    # ------------------------------------------------------------
    # Requests creating several records
    # ------------------------------------------------------------

    def test_create_request_in_parts(self):
        # the agent reads the parts of a request creating several records: one step per part
        _calls, mock = mock_values(lambda prompt: {"name": "Part Two" if "to create now: create a contact Part Two" in prompt else "Part One"})
        parts = [{'text': "create a contact Part One", 'target': "contact"},
                 {'text': "create a contact Part Two", 'target': "contact"}]
        with mock:
            plan = self._ask("create a contact Part One and a contact Part Two",
                             intent={'intent': 'create', 'parts': parts})['messages'][1]['result']
        self.assertEqual(plan['type'], 'plan')
        self.assertEqual(len(plan['steps']), 2)

    def test_several_records_linked_to_the_ones_before(self):
        # a record bearing the name of the one the request creates is not the one it links to
        existing = self.env['res.partner'].create({'name': "Orbit Labs", 'is_company': True})

        def values(prompt):
            if "Request: create a company Orbit Labs" in prompt:
                return {'name': "Orbit Labs", 'email': "hello@orbit.example.com"}
            # the values of a part are only those of that part
            self.assertIn('Created just before, by the same request: Contact "Orbit Labs"', prompt)
            return {'name': "Ann Lee", 'parent_id': "Orbit Labs", 'email': "hello@orbit.example.com"}

        calls, mock = mock_values(values)
        with mock:
            message = self._ask(
                "create a company Orbit Labs, hello@orbit.example.com, and create a contact Ann Lee at that company",
                intent={'intent': 'create', 'parts': [
                    {'text': "create a company Orbit Labs, hello@orbit.example.com", 'target': "contact"},
                    {'text': "create a contact Ann Lee at that company", 'target': "contact", 'refers_to': [1]},
                ]})['messages'][1]
        plan = message['result']
        self.assertEqual(len(calls), 2)
        self.assertEqual((plan['type'], plan['state'], plan['current']), ('plan', 'draft', 0))
        company_step, contact_step = plan['steps']
        self.assertIn("Orbit Labs", company_step['title'])
        self.assertEqual(contact_step['values']['parent_id'], {'$step': 0})
        self.assertNotIn('email', contact_step['values'], "a value of another part is not this record's")
        self.assertIn("Orbit Labs (new)", [field['value'] for field in contact_step['fields']])

        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        first = Conversation.create_draft_record(message['id'])['result']
        company = self.env['res.partner'].browse(first['steps'][0]['res_id'])
        self.assertNotEqual(company, existing)
        last = Conversation.create_draft_record(message['id'])['result']
        self.assertEqual(last['state'], 'created')
        self.assertEqual(self.env['res.partner'].browse(last['res_id']).parent_id, company)

    def test_part_adding_to_the_record_before(self):
        # "add him to..." creates no record of its own: it stays with the part before it
        calls, mock = mock_values({'name': "Solo Person", 'category_id': ["Zeta VIP"]})
        with mock:
            draft = self._ask("create a contact Solo Person and add him to the Zeta VIP tag", intent={
                'intent': 'create', 'parts': [{'text': "create a contact Solo Person", 'target': "contact"},
                                              {'text': "and add him to the Zeta VIP tag", 'target': ""}],
            })['messages'][1]['result']
        self.assertEqual(draft['type'], 'draft')
        self.assertEqual(len(calls), 1)
        self.assertIn("Request: create a contact Solo Person and add him to the Zeta VIP tag", calls[0])

    # ------------------------------------------------------------
    # Several records: what the agent read of the parts
    # ------------------------------------------------------------

    def test_parts_link_only_to_the_parts_they_refer_to(self):
        # "two contacts: Ann Lee... and Bob Stone...": Bob is no contact of Ann, though the AI may say so
        def values(prompt):
            if "Request: Bob Stone" in prompt:
                self.assertNotIn("Created just before", prompt, "no earlier record is offered to link to")
                return {'name': "Bob Stone", 'phone': "9876543210", 'parent_id': "Ann Lee"}
            return {'name': "Ann Lee", 'email': "ann@example.com"}
        _calls, mock = mock_values(values)
        with mock:
            message = self._ask("add two contacts: Ann Lee with email ann@example.com and Bob Stone with phone "
                                "9876543210", intent={'intent': 'create', 'parts': [
                                    {'text': "Ann Lee with email ann@example.com", 'target': "contact",
                                     'refers_to': []},
                                    {'text': "Bob Stone with phone 9876543210", 'target': "contact", 'refers_to': []},
                                ]})['messages'][1]
        plan = message['result']
        self.assertEqual(len(plan['steps']), 2)
        self.assertNotIn('parent_id', plan['steps'][1]['values'])
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        Conversation.create_draft_record(message['id'])
        last = Conversation.create_draft_record(message['id'])
        self.assertEqual(last['content'], 'All 2 records created: "Ann Lee", "Bob Stone".')

    def test_understood_parts_are_checked(self):
        Assistant = self.env['ai.chat.assistant']
        question = "create a project Apollo and a task Design in that project"
        intent = Assistant._clean_intent({'intent': 'create', 'parts': [
            {'text': "create a project Apollo", 'target': "project", 'refers_to': []},
            {'text': "a task Design in that project", 'target': "task", 'refers_to': [0]},
        ]}, question)
        # numbered from 0 by the AI: still the first part
        self.assertEqual([part['refers_to'] for part in intent['parts']], [[], [0]])
        self.assertTrue(all(part['verbatim'] for part in intent['parts']))
        intent = Assistant._clean_intent({'intent': 'create', 'parts': [
            {'text': "create the Apollo project", 'target': "project"},
            {'text': "a task Design in that project", 'target': "task", 'refers_to': [1]},
        ]}, question)
        self.assertEqual([part['verbatim'] for part in intent['parts']], [False, True], "a part not written so")
        self.assertEqual(intent['parts'][1]['refers_to'], [0])
        # a single part is the record of the whole request, never one of its lines
        intent = Assistant._clean_intent({'intent': 'create', 'target': "sales order", 'parts': [
            {'text': "2 chairs", 'target': "product"}]}, "create a sales order for Azure with 2 chairs")
        self.assertEqual((intent['parts'], intent['target']), ([], "sales order"))

    def test_record_marked_new_that_exists_is_linked(self):
        # the AI marks an existing tag as new: it is linked, not created twice
        _calls, mock = mock_values({'name': "Old Tag Person", 'category_id': [{'$new': "Zeta VIP"}]})
        with mock:
            draft = self._ask("create a contact Old Tag Person with tag Zeta VIP")['messages'][1]['result']
        self.assertEqual(draft['type'], 'draft', "no plan creating the tag first")
        self.assertEqual(draft['values']['category_id'], [[6, 0, [self.tag.id]]])

    def test_settings_record_never_chosen_over_a_usual_one(self):
        # "a company" matches the companies of the database best: the contact, created from a menu of the
        # apps, is chosen without asking
        settings = self.env.ref('base.menu_administration').name
        companies = dict(COMPANY, path=f"{settings}/Users & Companies/Companies", menu_names=["Companies"])
        contacts = dict(CONTACT, score=3, menu_names=["Contacts"])
        admin = new_test_user(self.env, login='ai_create_admin', groups='base.group_system,base.group_partner_manager,'
                                                                  'ai_chat_pro.group_ai_chat_user')
        calls, decisions_mock = mock_decisions(record='option_1')
        _calls, mock = mock_values({'name': "Zeta Firm", 'company_type': "company"})
        with mock, decisions_mock:
            draft = self._ask("create a company Zeta Firm", candidates=(companies, contacts), user=admin,
                              intent={'intent': 'create', 'target': "company"})['messages'][1]['result']
        self.assertEqual(draft['model'], 'res.partner')
        self.assertFalse(calls, "no decision needed")

    def test_value_written_but_not_checked_is_said(self):
        # "rate for the euro, then the dollar": the AI quotes "then" for a date, a word saying none: left to
        # the user, and said; "the day after tomorrow" says a date: set
        quoted = {'name': "then"}

        def olg_chat(self_, prompt):
            return json.dumps({'values': {'name': "2026-10-16"}, 'from': quoted})
        usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'cost': 0.0, 'ai_called': False}
        Assistant = self.env['ai.chat.assistant'].with_user(self.env.ref('base.user_admin'))
        with patch.object(AiChatAssistant, '_olg_chat', olg_chat):
            draft = Assistant._build_draft("a rate for the euro, then the dollar", 'res.currency.rate', "Rate", usage)
            self.assertNotIn('name', draft['values'])
            self.assertTrue(any("Date" in warning for warning in draft['warnings']), draft['warnings'])
            quoted['name'] = "the day after tomorrow"
            draft = Assistant._build_draft("a rate of the day after tomorrow", 'res.currency.rate', "Rate", usage)
            self.assertEqual(draft['values'].get('name'), "2026-10-16")

    # ------------------------------------------------------------
    # The records a request names: found, created, or chosen by the user
    # ------------------------------------------------------------

    def test_several_matching_records_are_chosen_by_the_user(self):
        # "Zeta Twin" matches two contacts: the user chooses, nothing is created or picked
        self.env['res.partner'].create([{'name': "Zeta Twin North"}, {'name': "Zeta Twin South"}])
        _calls, mock = mock_values({'name': "Twin Child", 'parent_id': "Zeta Twin"})
        with mock:
            message = self._ask("create a contact Twin Child working at Zeta Twin")['messages'][1]
        self.assertFalse(message['result'])
        self.assertIn('Several Related Company match "Zeta Twin"', message['content'])
        self.assertEqual(message['suggestions'], ["create a contact Twin Child working at Zeta Twin North",
                                                  "create a contact Twin Child working at Zeta Twin South"])
        # the request naming one exactly: that one
        _calls, mock = mock_values({'name': "Twin Child", 'parent_id': "Zeta Twin North"})
        with mock:
            draft = self._ask("create a contact Twin Child working at Zeta Twin North")['messages'][1]['result']
        self.assertEqual(draft['type'], 'draft')
        self.assertEqual(self.env['res.partner'].browse(draft['values']['parent_id']).name, "Zeta Twin North")

    def test_record_found_by_its_words(self):
        # "zeta solo 64 gb" is the contact "Zeta Solo 64GB": found word by word, not created again
        solo = self.env['res.partner'].create({'name': "Zeta Solo 64GB Traders", 'is_company': True})
        _calls, mock = mock_values({'name': "Solo Buyer", 'parent_id': "zeta solo 64 gb traders"})
        with mock:
            draft = self._ask("create a contact Solo Buyer working at zeta solo 64 gb traders")['messages'][1]['result']
        self.assertEqual(draft['type'], 'draft', "no plan creating the company")
        self.assertEqual(draft['values']['parent_id'], solo.id)

    def test_pieces_of_the_record_asked_are_no_records_of_their_own(self):
        # "a contact with the new tag Zeta Piece": the agent read the contact and the tag as parts, the tag is
        # a record the contact needs, drafted first, not a record asked for on its own
        tag = {'model': 'res.partner.category', 'label': "Contact Tag", 'score': 9, 'path': 'Contacts', 'domain': ''}

        def find_candidates(self_, keywords):
            return [tag] if 'tag' in keywords else [CONTACT]

        def values(prompt):
            if 'Only the Contact Tag "Zeta Piece"' in prompt:
                return {'name': "Zeta Piece"}
            return {'name': "Piece Person", 'category_id': [{'$new': "Zeta Piece"}]}
        _calls, mock = mock_values(values)
        _understood, intent_mock = mock_intent(intent='create', target='contact', parts=[
            {'text': "create a contact Piece Person", 'target': "contact person"},
            {'text': "with the new tag Zeta Piece", 'target': "tag"},
        ])
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        with mock, intent_mock, patch.object(AiChatAssistant, '_find_candidates', find_candidates):
            plan = Conversation.ask_question(
                False, "create a contact Piece Person with the new tag Zeta Piece")['messages'][1]['result']
        self.assertEqual(plan['type'], 'plan')
        self.assertEqual([step['model'] for step in plan['steps']], ['res.partner.category', 'res.partner'])
        self.assertNotIn('several', plan, "the tag is a record the contact needs")

    def test_record_that_can_not_be_created_is_said(self):
        # a lead, without the app of leads: said, and none of the records it needs is created
        _calls, mock = mock_values({'name': "Cybrosys"})
        _understood, intent_mock = mock_intent(intent='create', target='lead', parts=[
            {'text': "create lead", 'target': "lead"}, {'text': "for the new customer cybrosys", 'target': "contact"}])
        Conversation = self.env['ai.chat.conversation'].with_user(self.user)
        with mock, intent_mock, patch.object(AiChatAssistant, '_find_candidates',
                                             lambda self_, keywords: [] if 'lead' in keywords else [CONTACT]):
            message = Conversation.ask_question(False, "create lead for the new customer cybrosys")['messages'][1]
        self.assertFalse(message['result'])
        self.assertIn("I can not create a lead", message['content'])
