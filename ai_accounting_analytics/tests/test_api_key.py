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
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import Form, tagged

from odoo.addons.ai_accounting_analytics.llm import ADAPTERS

from .common import AiAccountingCommon, FakeAdapter


@tagged('post_install', '-at_install')
class TestApiKeyModel(AiAccountingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.key = cls.env['ai.accounting.api.key'].search([('user_id', '=', cls.env.uid)])
        cls.gemini_flash = cls.env.ref('ai_accounting_analytics.model_gemini_flash')
        cls.claude = cls.env.ref('ai_accounting_analytics.model_claude_haiku')

    def test_form_proposes_provider_models_only(self):
        with Form(self.env['ai.accounting.api.key'].with_user(self.env.user)) as form:
            form.provider_id = self.env.ref('ai_accounting_analytics.provider_anthropic')
            self.assertEqual(form.model_id.provider_id, form.provider_id)
            form.new_api_key = 'sk-ant-test-0000000'
            form.model_id = self.claude
        with self.assertRaises(ValidationError):
            self.key.model_id = self.claude

    def test_key_model_is_the_user_default(self):
        self.assertEqual(self.Chat._ai_default_model(), self.ai_model, "Company default")
        self.key.model_id = self.gemini_flash
        self.assertEqual(self.Chat._ai_default_model(), self.gemini_flash)
        self.assertEqual(self.Chat.ai_get_bootstrap()['default_model_id'], self.gemini_flash.id)
        chat, _message = self.Chat._ai_prepare_turn("Hello")
        self.assertEqual(chat.model_id, self.gemini_flash)

    def test_model_of_another_provider_key(self):
        """Only a Claude key: its chosen model wins over the Gemini default."""
        self.key.unlink()
        self.env['ai.accounting.api.key'].create({
            'provider_id': self.claude.provider_id.id, 'model_id': self.claude.id,
            'new_api_key': 'sk-ant-test-0000000'})
        self.assertEqual(self.Chat._ai_default_model(), self.claude)

    def test_key_without_model_for_another_provider(self):
        self.key.unlink()
        provider = self.claude.provider_id
        self.env['ai.accounting.api.key'].create({
            'provider_id': provider.id, 'new_api_key': 'sk-ant-test-0000000'})
        self.assertEqual(self.Chat._ai_default_model(), provider.model_ids[0])

    def test_archived_key_model_is_ignored(self):
        self.key.model_id = self.gemini_flash
        self.gemini_flash.active = False
        self.assertEqual(self.Chat._ai_default_model(), self.ai_model)

    def test_connection_checks_selected_model(self):
        self.key.model_id = self.gemini_flash
        with patch.dict(ADAPTERS, {'gemini': FakeAdapter}):
            result = self.key.action_test_connection()
            self.assertEqual(result['params']['type'], 'warning')
            self.assertIn('gemini-3.8-flash', result['params']['message'])
            self.gemini_flash.technical_name = 'fake-model'
            result = self.key.action_test_connection()
            self.assertEqual(result['params']['type'], 'success')
