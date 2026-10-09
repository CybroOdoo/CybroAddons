# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged

from .common import AiAccountingCommon, answer


@tagged('post_install', '-at_install')
class TestSecurity(AiAccountingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_chief = new_test_user(
            cls.env, login='other_chief', group_ids=[cls.chief_group.id],
            company_id=cls.env.company.id)
        cls.accountant = new_test_user(
            cls.env, login='plain_accountant',
            group_ids=[cls.env.ref('account.group_account_user').id],
            company_id=cls.env.company.id)

    def test_api_key_never_readable(self):
        Key = self.env['ai.accounting.api.key'].with_user(self.other_chief)
        key = Key.create({'provider_id': self.provider.id, 'new_api_key': 'sk-other-secret-9876'})
        self.assertEqual(key.api_key_hint, 'sk-…9876')
        self.assertNotIn('api_key', Key.fields_get())
        with self.assertRaises(AccessError):
            key.read(['api_key'])
        self.assertEqual(self.provider.with_user(self.other_chief)._get_user_api_key(),
                         'sk-other-secret-9876')

    def test_keys_and_chats_are_personal(self):
        with self.fake_llm(answer("Hi.")):
            chat, _events = self.ask("Hello")
        Key = self.env['ai.accounting.api.key'].with_user(self.other_chief)
        self.assertFalse(Key.search([]))
        Chat = self.Chat.with_user(self.other_chief)
        self.assertFalse(Chat.search([('id', '=', chat.id)]))
        with self.assertRaises(AccessError):
            chat.with_user(self.other_chief).read(['name'])
        Usage = self.env['ai.accounting.usage'].with_user(self.other_chief)
        self.assertFalse(Usage.search([]))
        with self.assertRaises(UserError):
            self.provider.with_user(self.other_chief)._get_user_api_key()

    def test_chief_accountant_only(self):
        self.accountant.sudo().ai_accounting_consent_date = '2026-01-01 00:00:00'
        with self.assertRaises(AccessError):
            self.Chat.with_user(self.accountant)._ai_prepare_turn("Hello")

    def test_consent_required(self):
        Chat = self.Chat.with_user(self.other_chief)
        self.env['ai.accounting.api.key'].with_user(self.other_chief).create({
            'provider_id': self.provider.id, 'new_api_key': 'other-user-key-0000'})
        with self.assertRaises(UserError):
            Chat._ai_prepare_turn("Hello")
        Chat.ai_accept_consent()
        self.assertTrue(self.other_chief.ai_accounting_consent_date)
        chat, _message = Chat._ai_prepare_turn("Hello")
        self.assertEqual(chat.user_id, self.other_chief)

    def test_api_key_required(self):
        self.env['ai.accounting.api.key'].search([]).unlink()
        with self.assertRaises(UserError):
            self.Chat._ai_prepare_turn("Hello")

    def test_export_only_whitelisted_reports(self):
        with self.fake_llm(answer("Hi.")):
            chat, _events = self.ask("Hello")
        message = chat.message_ids.filtered(lambda m: m.role == 'assistant')
        message.parts = [{'type': 'table', 'export': {
            'model': 'res.users', 'vals': {'login': 'evil'}, 'pdf': 'unlink'}}]
        with self.assertRaises(UserError):
            chat.ai_export(message.id, 0, 'pdf')
        with self.assertRaises(UserError):
            chat.ai_export(message.id, 5, 'pdf')

    def test_question_validation(self):
        with self.assertRaises(UserError):
            self.Chat._ai_prepare_turn("   ")
        with self.assertRaises(UserError):
            self.Chat._ai_prepare_turn("x" * 5000)
