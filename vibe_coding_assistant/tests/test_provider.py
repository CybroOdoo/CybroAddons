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

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.vibe_coding_assistant.services.provider_base import (
    AIAuthError,
    AINetworkError,
    AINotFoundError,
    AIProviderError,
)

from .common import VibeCommon

GET_PROVIDER = "odoo.addons.vibe_coding_assistant.models.ai_provider.get_provider"


@tagged("post_install", "-at_install")
class TestAIProvider(VibeCommon):

    def setUp(self):
        super().setUp()
        # action_refresh_models uses the *current* user's own API key and
        # needs write access to the provider, so it runs as the admin env user.
        self.env["ai.provider.user.config"].create({
            "user_id": self.env.uid,
            "provider_id": self.provider.id,
            "api_key": "admin-key",
            "selected_model": "model-1",
        })

    def test_code_unique(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(Exception), \
                self.env.cr.savepoint():
            self.env["ai.provider"].create({
                "name": "Dup",
                "code": self.provider.code,
                "default_model": "m",
                "available_models": "m",
                "api_base_url": "https://example.invalid",
            })

    def test_single_default(self):
        # Seed data already ships a default provider; clear it first.
        self.env["ai.provider"].search([("is_default", "=", True)]).write(
            {"is_default": False})
        self.provider.is_default = True
        with self.assertRaises(ValidationError):
            self.provider_2.is_default = True

    def test_conversation_stats(self):
        conv = self._make_conversation(provider_config_id=self.config_a.id)
        self.env["vibe.message"].create({
            "conversation_id": conv.id, "role": "assistant", "content": "x",
            "tokens_input": 5, "tokens_output": 7, "tokens_used": 12,
        })
        self.provider.invalidate_recordset()
        self.assertEqual(self.provider.conversation_count, 1)
        self.assertEqual(self.provider.tokens_used_total, 12)

    def test_action_view_conversations(self):
        action = self.provider.action_view_conversations()
        self.assertEqual(action["res_model"], "vibe.conversation")
        self.assertIn(("provider_config_id.provider_id", "=", self.provider.id),
                      action["domain"])

    def test_refresh_requires_personal_key(self):
        with self.assertRaises(UserError):
            self.provider_2.action_refresh_models()

    def test_refresh_success_keeps_default(self):
        mock = patch(GET_PROVIDER).start()
        self.addCleanup(patch.stopall)
        mock.return_value.list_models.return_value = ["model-1", "model-3"]
        # The action reads the *current user's* config, so act as user A.
        res = self.provider.action_refresh_models()
        self.assertEqual(res["tag"], "display_notification")
        self.assertEqual(self.provider.available_models, "model-1\nmodel-3")
        self.assertEqual(self.provider.default_model, "model-1")

    def test_refresh_changes_default_when_missing(self):
        mock = patch(GET_PROVIDER).start()
        self.addCleanup(patch.stopall)
        mock.return_value.list_models.return_value = ["model-9"]
        self.provider.action_refresh_models()
        self.assertEqual(self.provider.default_model, "model-9")

    def test_refresh_errors_become_user_errors(self):
        mock = patch(GET_PROVIDER).start()
        self.addCleanup(patch.stopall)
        errors = [
            AIAuthError("bad"), AINotFoundError("nf"), AINetworkError("net"),
            NotImplementedError(), AIProviderError("generic"),
        ]
        for err in errors:
            with self.subTest(error=type(err).__name__):
                mock.return_value.list_models.side_effect = err
                with self.assertRaises(UserError):
                    self.provider.action_refresh_models()

    def test_refresh_empty_list(self):
        mock = patch(GET_PROVIDER).start()
        self.addCleanup(patch.stopall)
        mock.return_value.list_models.return_value = []
        with self.assertRaises(UserError):
            self.provider.action_refresh_models()
