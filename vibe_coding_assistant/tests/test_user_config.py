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

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.vibe_coding_assistant.services.provider_base import (
    AIAuthError,
    AINetworkError,
    AINotFoundError,
    AIProviderError,
    AIQuotaError,
)

from .common import VibeCommon

GET_PROVIDER = (
    "odoo.addons.vibe_coding_assistant.models.ai_provider_user_config.get_provider"
)


@tagged("post_install", "-at_install")
class TestUserConfig(VibeCommon):

    def _config(self, provider, user=None, **vals):
        values = {
            "user_id": (user or self.user_b).id,
            "provider_id": provider.id,
            "api_key": "key",
            "selected_model": "model-1",
        }
        values.update(vals)
        return self.env["ai.provider.user.config"].create(values)

    def test_name_compute(self):
        self.assertEqual(self.config_a.name, "Test Provider (model-1)")
        blank = self.env["ai.provider.user.config"].new({})
        blank._compute_name()
        self.assertTrue(blank.name)
        provider_only = self.env["ai.provider.user.config"].new(
            {"provider_id": self.provider.id})
        provider_only._compute_name()
        self.assertEqual(provider_only.name, "Test Provider")

    def test_onchange_provider_prefills_model(self):
        rec = self.env["ai.provider.user.config"].new(
            {"provider_id": self.provider_2.id})
        rec._onchange_provider_id()
        self.assertEqual(rec.selected_model, "model-x")

    def test_onchange_invalidates_test_result(self):
        rec = self._config(self.provider)
        rec.write({"last_test_state": "success", "last_test_message": "ok"})
        rec._onchange_invalidate_test()
        self.assertEqual(rec.last_test_state, "untested")
        self.assertFalse(rec.last_test_message)

    def test_unique_user_provider(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(Exception), \
                self.env.cr.savepoint():
            self._config(self.provider, user=self.user_a)

    def test_activation_deactivates_siblings(self):
        second = self._config(self.provider_2, user=self.user_a)
        second.action_activate()
        self.assertTrue(second.is_active)
        self.assertFalse(self.config_a.is_active)

    def test_activate_already_active_and_deactivate(self):
        res = self.config_a.action_activate()
        self.assertEqual(res["params"]["type"], "info")
        res = self.config_a.action_deactivate()
        self.assertFalse(self.config_a.is_active)
        self.assertEqual(res["params"]["type"], "info")

    def test_get_active_config_and_info(self):
        Config = self.env["ai.provider.user.config"]
        self.assertEqual(Config.get_active_config_for_user(self.user_a.id),
                         self.config_a)
        info = Config.with_user(self.user_a).get_active_provider_info()
        self.assertEqual(info["provider_code"], "gemini_test")
        self.assertEqual(info["model"], "model-1")
        self.assertFalse(Config.with_user(self.user_b).get_active_provider_info())

    def test_token_totals(self):
        conv = self._make_conversation(provider_config_id=self.config_a.id)
        self.env["vibe.message"].create({
            "conversation_id": conv.id, "role": "assistant", "content": "x",
            "tokens_input": 4, "tokens_output": 6, "tokens_used": 10,
        })
        self.config_a.invalidate_recordset()
        self.assertEqual(self.config_a.tokens_used_input, 4)
        self.assertEqual(self.config_a.tokens_used_output, 6)
        self.assertEqual(self.config_a.tokens_used_total, 10)
        self.assertEqual(self.config_a.tokens_conversation_count, 1)

    def test_connection_requires_key(self):
        rec = self._config(self.provider_2, user=self.user_a, api_key="   ")
        with self.assertRaises(UserError):
            rec.action_test_connection()

    def test_connection_success(self):
        with patch(GET_PROVIDER) as mock:
            mock.return_value.ping.return_value = "pong"
            res = self.config_a.action_test_connection()
        self.assertEqual(res["params"]["type"], "success")
        self.assertEqual(self.config_a.last_test_state, "success")
        self.assertIn("pong", self.config_a.last_test_message)

    def test_connection_failures_are_recorded(self):
        for err in (AIQuotaError("q"), AIAuthError("a"), AINotFoundError("n"),
                    AINetworkError("net"), AIProviderError("generic")):
            with self.subTest(error=type(err).__name__):
                with patch(GET_PROVIDER) as mock:
                    mock.return_value.ping.side_effect = err
                    res = self.config_a.action_test_connection()
                self.assertEqual(res["params"]["type"], "danger")
                self.assertEqual(self.config_a.last_test_state, "failed")
