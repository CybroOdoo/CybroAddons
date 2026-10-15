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
import json
from unittest.mock import patch

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.ai_chat_pro.models.ai_chat_assistant import AiChatAssistant
from odoo.addons.ai_chat_pro.models.ai_chat_import_repair import AiChatAssistant as AiChatRepair

from .test_ai_chat_pro import mock_intent

# the menu customers are created from sets their defaults (Sales > Customers makes them customers)
CONTACTS = {'model': 'res.partner', 'label': 'Contact', 'score': 9, 'path': 'Contacts', 'domain': '',
            'context': "{'default_function': 'Imported buyer', 'search_default_customer': 1}"}

CUSTOMERS_CSV = (
    "Name,Email,Town,Favourite colour\n"
    "Alpha Zeta Import,alpha@example.com,Kochi,blue\n"
    "Beta Zeta Import,beta@example.com,Pune,red\n"
)


@tagged('post_install', '-at_install')
class TestAiChatImport(TransactionCase):

    # what the agent understands of the messages of these tests
    INTENTS = {
        'create customers based on the attached file': {'intent': 'import', 'target': 'customers'},
        'create customers from the attached file': {'intent': 'import', 'target': 'customers'},
        'import these contacts': {'intent': 'import', 'target': 'contacts'},
        'import these states': {'intent': 'import', 'target': 'states'},
        'which towns are in this file?': {'intent': 'file'},
        'import the attached file': {'intent': 'import'},
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
            cls.env, login='ai_import_user', groups='base.group_user,base.group_partner_manager,'
                                                    'ai_chat_pro.group_ai_chat_user',
        )
        cls.other_user = new_test_user(cls.env, login='ai_import_other', groups='base.group_user,ai_chat_pro.group_ai_chat_user')
        cls.Conversation = cls.env['ai.chat.conversation'].with_user(cls.user)

    def _upload(self, content, name="customers.csv", user=None):
        Conversation = self.env['ai.chat.conversation'].with_user(user or self.user)
        return Conversation.upload_chat_attachment(name, base64.b64encode(content.encode()).decode())

    def _ask(self, question, attachment_ids, olg_answer=None, candidates=(CONTACTS,)):
        prompts = []

        def olg_chat(self_, prompt):
            prompts.append(prompt)
            return olg_answer(prompt) if callable(olg_answer) else (olg_answer or "{}")
        with patch.object(AiChatAssistant, '_olg_chat', olg_chat), \
                patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: list(candidates)):
            answer = self.Conversation.ask_question(False, question, False, attachment_ids)
        return answer['messages'], prompts

    def test_upload(self):
        attachment = self._upload(CUSTOMERS_CSV)
        self.assertEqual(attachment['name'], "customers.csv")
        record = self.env['ir.attachment'].browse(attachment['id'])
        self.assertEqual((record.create_uid, record.res_model), (self.user, False))
        with self.assertRaisesRegex(UserError, "Only spreadsheets"):
            self._upload("hello", name="notes.txt")
        # files are sent by their sender only, once
        with self.assertRaises(AccessError):
            self.env['ai.chat.conversation'].with_user(self.other_user).ask_question(
                False, "create customers from the file", False, [attachment['id']])

    def test_import_customers(self):
        attachment = self._upload(CUSTOMERS_CSV)
        mapping = json.dumps({'mapping': {'Town': 'city', 'Favourite colour': None}})
        messages, prompts = self._ask("create customers based on the attached file", [attachment['id']],
                                      olg_answer=mapping)
        question, answer = messages
        self.assertEqual(question['attachments'][0]['name'], "customers.csv")
        self.assertFalse(answer['is_error'], answer['content'])
        draft = answer['result']
        self.assertEqual((draft['type'], draft['state'], draft['model'], draft['count']), ('import', 'draft', 'res.partner', 2))
        mapping = {column['column']: (column['field'], column['by']) for column in draft['mapping']}
        self.assertEqual(mapping['Name'], ("Name", 'odoo'))
        self.assertEqual(mapping['Town'], ("City", 'ai'), "a column Odoo does not match, matched by the AI")
        self.assertEqual(mapping['Favourite colour'], (False, False))
        self.assertIn("Favourite colour", answer['content'], "ignored columns are said")
        self.assertEqual(draft['error_count'], 0)
        self.assertEqual(draft['rows'][0][0], "Alpha Zeta Import")
        # the AI only sees the columns Odoo did not match, and their first values
        mapping_prompt = next(prompt for prompt in prompts if "Match each column" in prompt)
        self.assertIn("'Town'", mapping_prompt)
        self.assertNotIn("'Name'", mapping_prompt)
        # the test import created nothing
        Partner = self.env['res.partner']
        self.assertFalse(Partner.search([('name', 'like', 'Zeta Import')]))
        # the file now belongs to the question
        record = self.env['ir.attachment'].browse(attachment['id'])
        self.assertEqual((record.res_model, record.res_id), ('ai.chat.message', question['id']))

        created = self.Conversation.create_draft_record(answer['id'])
        self.assertEqual((created['result']['state'], created['result']['created']), ('created', 2))
        partners = Partner.search([('name', 'like', 'Zeta Import')], order='name')
        self.assertEqual(partners.mapped('city'), ["Kochi", "Pune"])
        self.assertEqual(partners.mapped('email'), ["alpha@example.com", "beta@example.com"])
        self.assertEqual(set(partners.mapped('function')), {"Imported buyer"}, "the defaults of the menu apply")
        self.assertEqual(partners.create_uid, self.user, "imported as the user asking")
        action = self.Conversation.get_import_records_action(answer['id'])
        self.assertEqual(action['domain'], [('id', 'in', partners.ids)])
        with self.assertRaisesRegex(UserError, "already created"):
            self.Conversation.create_draft_record(answer['id'])

    def test_name_column_matched_without_ai(self):
        # "Customer Name" is no field name Odoo matches: the name of the records is never left to the AI
        attachment = self._upload("Customer Name,Email\nDelta Zeta Import,delta@example.com\n")
        messages, _prompts = self._ask("create customers from the attached file", [attachment['id']],
                                       olg_answer='{"mapping": {}}')
        draft = messages[1]['result']
        self.assertEqual(draft['mapping'][0], {'column': "Customer Name", 'field': "Name", 'by': 'name'})
        self.assertEqual(draft['error_count'], 0)
        self.Conversation.create_draft_record(messages[1]['id'])
        self.assertTrue(self.env['res.partner'].search([('name', '=', "Delta Zeta Import")]))

    def test_repaired_import(self):
        # values Odoo can not read are repaired: nothing blocks the import
        vip = self.env['res.partner.category'].create({'name': "Zeta VIP"})
        india = self.env.ref('base.in')
        content = (
            "Name,Tags,Country,Is a Company,Date\n"
            "Epsilon Zeta Import,VIP customers,Indai,yes,31/12/2025\n"
            "Eta Zeta Import,Brand New Zeta Tag,Atlantis Nowhere,no,2026-01-15\n"
            ",Zeta VIP,India,no,\n"
        )
        attachment = self._upload(content)

        def olg_answer(prompt):
            if "Some values match no record" in prompt:
                return json.dumps({'values': {
                    'column_1': {'VIP customers': {'match': vip.id}, 'Brand New Zeta Tag': {'create': True}},
                    'column_2': {'Indai': {'match': india.id}, 'Atlantis Nowhere': {'empty': True}},
                }})
            return '{}'
        messages, prompts = self._ask("import these contacts", [attachment['id']], olg_answer=olg_answer)
        draft = messages[1]['result']
        self.assertFalse(messages[1]['is_error'], messages[1]['content'])
        fixes = " ".join(fix['text'] for fix in draft['fixes'])
        self.assertIn('"VIP customers" read as Zeta VIP', fixes)
        self.assertIn('"Brand New Zeta Tag" does not exist and will be created', fixes)
        self.assertIn('"Indai" read as India', fixes)
        self.assertIn('"Atlantis Nowhere" matches no record and was left empty', fixes)
        # the row without a name fails: left out, the others are imported
        self.assertEqual((draft['count'], draft['total'], draft['skipped_count']), (2, 3, 1))
        self.assertEqual(draft['skipped'][0]['row'], 4, "the row of the file, its first line naming the columns")
        repair_prompt = next(prompt for prompt in prompts if "Some values match no record" in prompt)
        self.assertIn('value "Indai"', repair_prompt)
        self.assertIn(f'{india.id}="India"', repair_prompt, "the AI chooses among existing records")
        # nothing was created by the test imports
        self.assertFalse(self.env['res.partner.category'].search([('name', '=', "Brand New Zeta Tag")]))

        created = self.Conversation.create_draft_record(messages[1]['id'])['result']
        self.assertEqual((created['created'], created['skipped_count']), (2, 1))
        epsilon = self.env['res.partner'].search([('name', '=', "Epsilon Zeta Import")])
        eta = self.env['res.partner'].search([('name', '=', "Eta Zeta Import")])
        self.assertEqual((epsilon.category_id, epsilon.country_id, epsilon.is_company), (vip, india, True))
        self.assertEqual(eta.category_id.name, "Brand New Zeta Tag")
        self.assertFalse(eta.country_id)

    def test_required_field_default(self):
        # states need a country the file does not give: the AI chooses it among the countries
        manager = new_test_user(self.env, login='ai_import_admin',
                                groups='base.group_system,ai_chat_pro.group_ai_chat_user')
        attachment = self.env['ai.chat.conversation'].with_user(manager).upload_chat_attachment(
            "states.csv", base64.b64encode(b"Name,Code\nZeta North,ZN\nZeta South,ZS\n").decode())
        india = self.env.ref('base.in')
        states = {'model': 'res.country.state', 'label': 'Fed. States', 'score': 9, 'path': '', 'domain': '', 'context': ''}

        def olg_answer(prompt):
            if "Some values match no record" in prompt:
                self.assertIn("default_country_id", prompt)
                return json.dumps({'defaults': {'default_country_id': india.id}})
            return "{}"
        with patch.object(AiChatAssistant, '_olg_chat', lambda self_, prompt: olg_answer(prompt)), \
                patch.object(AiChatAssistant, '_find_candidates', lambda self_, keywords: [states]), \
                patch.object(AiChatRepair, '_get_missing_required_fields',
                             lambda self_, *args: {'country_id': [{'id': india.id, 'name': "India"}]}):
            Conversation = self.env['ai.chat.conversation'].with_user(manager)
            message = Conversation.ask_question(False, "import these states", False, [attachment['id']])['messages'][1]
            self.assertIn("Country, required and not in the file: set to India.", message['result']['fixes'][0]['text'])
            Conversation.create_draft_record(message['id'])
        self.assertEqual(self.env['res.country.state'].search([('code', 'in', ('ZN', 'ZS'))]).country_id, india)

    def test_matches_merging_values_are_rejected(self):
        Repair = self.env['ai.chat.assistant']
        field = self.env['res.partner']._fields['category_id']
        bank = [{'id': 5, 'name': "Bank"}]
        pending = {'1000- Aripero': bank, '1002- Carenage': bank, 'Units': [{'id': 7, 'name': "Units"}]}
        checked = Repair._check_matches(field, pending, {
            '1000- Aripero': {'match': 5}, '1002- Carenage': {'match': 5}, 'Units': {'match': 7},
        })
        self.assertEqual(checked['1000- Aripero'].get('create'), True, "two codes are not one record")
        self.assertNotIn('match', checked['1002- Carenage'])
        self.assertEqual(checked['Units'], {'match': 7})

    def test_create_values_checked(self):
        Repair = self.env['ai.chat.assistant']
        field = self.env['res.partner']._fields['category_id']
        spec = {'mode': 'values', 'fields': {'code': ("Code", 'char', None), 'color': ("Color", 'integer', None),
                                             'kind': ("Kind", 'selection', ['asset_cash', 'expense'])}}
        self.assertEqual(
            Repair._get_create_values(field, "1000- Aripero", spec, {'name': "Aripero", 'code': "1000", 'color': "3",
                                                                     'kind': 'asset_cash'}),
            {'name': "Aripero", 'code': "1000", 'color': 3, 'kind': 'asset_cash'},
        )
        self.assertIsNone(Repair._get_create_values(field, "X", spec, {'kind': 'not_a_kind', 'color': 1}),
                          "a required value missing or invalid: not created")
        self.assertEqual(Repair._get_create_values(field, "Tag", {'mode': 'name'}, True), {'name': "Tag"})

    def test_values_cleaned(self):
        from odoo.addons.ai_chat_pro.models.ai_chat_import_repair import _parse_date, _parse_number
        cases = {"1,234.50": 1234.5, "1.234,50": 1234.5, "₹ 1,200": 1200.0, "(50)": -50.0, "12,5": 12.5,
                 "15%": 15.0, "-7": -7.0, "abc": None, "": None}
        for text, number in cases.items():
            self.assertEqual(_parse_number(text), number, text)
        self.assertEqual(str(_parse_date("31/12/2025").date()), "2025-12-31")
        self.assertEqual(str(_parse_date("2026-01-15").date()), "2026-01-15")
        self.assertEqual(str(_parse_date("15 Jan 2026").date()), "2026-01-15")
        self.assertIsNone(_parse_date("not a date"))

    def test_question_about_the_file(self):
        attachment = self._upload(CUSTOMERS_CSV)
        messages, prompts = self._ask("which towns are in this file?", [attachment['id']],
                                      olg_answer="Kochi and Pune.")
        self.assertEqual(messages[1]['content'], "Kochi and Pune.")
        self.assertFalse(messages[1]['result'])
        self.assertIn("Beta Zeta Import", prompts[0], "the AI reads the rows")

    def test_import_without_kind_of_records(self):
        attachment = self._upload(CUSTOMERS_CSV)
        messages, _prompts = self._ask("import the attached file", [attachment['id']], candidates=())
        self.assertTrue(messages[1]['is_error'])
        self.assertIn("Which kind of records", messages[1]['content'])
