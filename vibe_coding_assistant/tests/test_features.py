# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: FATHIMA SHALFA P (odoo@cybrosys.com)
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
###############################################################################
"""Tests for refinement, connection testing, model refresh, the dashboard
and the conversation exporter. The AI provider is always mocked."""
import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import new_test_user, tagged
from odoo.tools import mute_logger

from ..services.conversation_exporter import build_export
from ..services.prompt_builder import build_refinement
from ..services.provider_base import (
    AIAuthError,
    AINetworkError,
    AINotFoundError,
    AIProviderError,
    AIQuotaError,
)
from .test_models import PROVIDER_PATH, VibeCommon
from .test_services import _envelope

ADDON = "odoo.addons.vibe_coding_assistant"
CONFIG_PROVIDER_PATH = ADDON + ".models.ai_provider_user_config.get_provider"
CATALOG_PROVIDER_PATH = ADDON + ".models.ai_provider.get_provider"


@tagged("post_install", "-at_install")
class TestRefinement(VibeCommon):

    def setUp(self):
        super().setUp()
        self.conv = self.env["vibe.conversation"].with_user(self.user).create({})

    def _send(self, method, content, raw=None, error=None):
        provider = self._mock_provider(raw=raw, error=error)
        with patch(PROVIDER_PATH, return_value=provider), \
                mute_logger(ADDON + ".models.vibe_conversation"):
            return getattr(self.conv, method)(content), provider

    def test_refine_requires_content_and_module(self):
        with self.assertRaises(UserError):
            self.conv.action_refine_module("  ")
        with self.assertRaises(UserError):
            self.conv.action_refine_module("Add a field")

    def test_refine_requires_active_config(self):
        self._send("action_send_message", "Brand module", raw=json.dumps(_envelope()))
        self.config_gemini.is_active = False
        with self.assertRaises(UserError):
            self.conv.action_refine_module("Add a field")

    def test_refine_creates_linked_revision(self):
        self._send("action_send_message", "Brand module", raw=json.dumps(_envelope()))
        first = self.conv.generated_module_ids
        refined = _envelope(display_name="Product Brand v2")
        payload, provider = self._send(
            "action_refine_module", "Add a description field", raw=json.dumps(refined))

        user_prompt = provider.generate.call_args.args[1]
        self.assertIn("PREVIOUS MODULE STATE", user_prompt)
        self.assertIn("Add a description field", user_prompt)

        second = self.conv.generated_module_ids - first
        self.assertEqual(len(second), 1)
        self.assertEqual(second.parent_module_id, first)
        self.assertEqual(second.revision_number, 2)
        self.assertTrue(second.is_refinement)
        self.assertEqual(first.child_module_ids, second)
        self.assertEqual(second.validation_state, "valid")
        self.assertEqual(payload["conversation"]["latest_module_revision"], 2)
        self.assertEqual(payload["messages"][-1]["generated_module_parent_id"], first.id)
        self.assertEqual(self.conv.tokens_total, 60)

    def test_refine_provider_error_and_bad_response(self):
        self._send("action_send_message", "Brand module", raw=json.dumps(_envelope()))
        payload, _p = self._send("action_refine_module", "More",
                                 error=AIProviderError("down"))
        self.assertIn("down", payload["messages"][-1]["content"])
        payload, _p = self._send("action_refine_module", "More", raw="not json")
        self.assertEqual(len(self.conv.generated_module_ids), 1)
        self.assertEqual(payload["messages"][-1]["role"], "assistant")

    def test_invalid_generation_is_flagged(self):
        broken = _envelope(files={"models/product_brand.py": "def x(:\n"})
        self._send("action_send_message", "Brand module", raw=json.dumps(broken))
        mod = self.conv.generated_module_ids
        self.assertEqual(mod.validation_state, "invalid")
        self.assertTrue(mod.get_validation_errors_list())

    def test_template_merge_failure_is_not_fatal(self):
        with patch(ADDON + ".models.vibe_conversation.merge_templates",
                   side_effect=OSError("disk")):
            self._send("action_send_message", "Brand module", raw=json.dumps(_envelope()))
        self.assertEqual(len(self.conv.generated_module_ids), 1)

    def test_load_messages_and_manifest_field(self):
        self._send("action_send_message", "Brand module", raw=json.dumps(_envelope()))
        mod = self.conv.generated_module_ids
        self.assertEqual(self.conv.load_messages()["conversation"]["id"], self.conv.id)
        self.assertEqual(self.conv._manifest_field(mod, "depends"), ["product"])
        mod.manifest_data = "{broken"
        self.assertFalse(self.conv._manifest_field(mod, "version"))
        self.assertFalse(self.conv._manifest_field(False, "version"))

    def test_long_message_truncates_title(self):
        content = "x" * 80
        self._send("action_send_message", content, raw=json.dumps(_envelope()))
        self.assertEqual(self.conv.name, "x" * 60 + "…")

    def test_build_refinement_prompt(self):
        system, user = build_refinement("  add field  ", {"technical_name": "a"},
                                        [{"path": "a.py", "content": "x"}])
        self.assertIn("add field", user)
        self.assertIn('"a.py"', user)
        self.assertTrue(system)


@tagged("post_install", "-at_install")
class TestConnectionTest(VibeCommon):

    def _ping(self, result=None, error=None):
        provider = MagicMock()
        if error:
            provider.ping.side_effect = error
        else:
            provider.ping.return_value = result
        with patch(CONFIG_PROVIDER_PATH, return_value=provider), \
                mute_logger(ADDON + ".models.ai_provider_user_config"):
            return self.config_gemini.with_user(self.user).action_test_connection()

    def test_success(self):
        action = self._ping(result="OK — 3 tokens")
        self.assertEqual(action["params"]["type"], "success")
        self.assertEqual(self.config_gemini.last_test_state, "success")
        self.assertIn("OK", self.config_gemini.last_test_message)
        self.assertTrue(self.config_gemini.last_test_date)

    def test_failures(self):
        for error, title in (
            (AIQuotaError("q"), "Quota or rate limit exceeded"),
            (AIAuthError("a"), "Invalid or unauthorised API key"),
            (AINotFoundError("n"), "Model not found"),
            (AINetworkError("net"), "Network error"),
            (AIProviderError("generic"), "Connection failed"),
        ):
            action = self._ping(error=error)
            self.assertEqual(action["params"]["title"], title)
            self.assertEqual(action["params"]["type"], "danger")
            self.assertEqual(self.config_gemini.last_test_state, "failed")

    def test_requires_key_and_model(self):
        self.config_gemini.api_key = " "
        with self.assertRaises(UserError):
            self.config_gemini.action_test_connection()
        draft = self.env["ai.provider.user.config"].new({
            "provider_id": self.claude.id, "api_key": "k", "selected_model": False})
        with self.assertRaises(UserError):
            draft.action_test_connection()

    def test_onchanges(self):
        config = self.env["ai.provider.user.config"].new({"provider_id": self.claude.id})
        config._onchange_provider_id()
        self.assertEqual(config.selected_model, self.claude.default_model)
        config.last_test_state = "success"
        config._onchange_invalidate_test()
        self.assertEqual(config.last_test_state, "untested")
        self.assertEqual(config.name, "%s (%s)" % (self.claude.name, self.claude.default_model))
        empty = self.env["ai.provider.user.config"].new({})
        self.assertEqual(empty.name, "Config")

    def test_activate_deactivate_notifications(self):
        config = self.config_gemini.with_user(self.user)
        self.assertEqual(config.action_activate()["params"]["type"], "info")
        self.assertEqual(config.action_deactivate()["params"]["type"], "info")
        self.assertFalse(config.is_active)
        self.assertFalse(self.env["ai.provider.user.config"].with_user(
            self.user).get_active_provider_info())

    def test_token_totals(self):
        conv = self.env["vibe.conversation"].create({
            "user_id": self.user.id, "provider_config_id": self.config_gemini.id})
        self.env["vibe.message"].create({
            "conversation_id": conv.id, "role": "assistant", "content": "x",
            "tokens_input": 4, "tokens_output": 6, "tokens_used": 10,
        })
        self.config_gemini.invalidate_recordset()
        self.assertEqual(self.config_gemini.tokens_used_total, 10)
        self.assertEqual(self.config_gemini.tokens_used_input, 4)
        self.assertEqual(self.config_gemini.tokens_conversation_count, 1)
        self.assertEqual(self.gemini.conversation_count, 1)
        self.assertEqual(self.gemini.tokens_used_total, 10)
        action = self.gemini.action_view_conversations()
        self.assertEqual(action["res_model"], "vibe.conversation")
        self.assertIn(("provider_config_id.provider_id", "=", self.gemini.id), action["domain"])


@tagged("post_install", "-at_install")
class TestRefreshModels(VibeCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = new_test_user(cls.env, login="vibe_admin", groups="base.group_system")
        cls.env["ai.provider.user.config"].create({
            "user_id": cls.admin.id,
            "provider_id": cls.gemini.id,
            "api_key": "admin-key",
            "selected_model": "gemini-2.5-flash",
        })

    def _refresh(self, models=None, error=None):
        provider = MagicMock()
        if error:
            provider.list_models.side_effect = error
        else:
            provider.list_models.return_value = models
        with patch(CATALOG_PROVIDER_PATH, return_value=provider):
            return self.gemini.with_user(self.admin).action_refresh_models()

    def test_refresh_keeps_default(self):
        self.gemini.default_model = "gemini-2.5-flash"
        action = self._refresh(["gemini-2.5-flash", "gemini-2.5-pro"])
        self.assertEqual(self.gemini.available_models, "gemini-2.5-flash\ngemini-2.5-pro")
        self.assertEqual(self.gemini.default_model, "gemini-2.5-flash")
        self.assertNotIn("no longer", action["params"]["message"])

    def test_refresh_replaces_missing_default(self):
        self.gemini.default_model = "gemini-1.0-retired"
        action = self._refresh(["gemini-2.5-pro"])
        self.assertEqual(self.gemini.default_model, "gemini-2.5-pro")
        self.assertIn("no longer", action["params"]["message"])

    def test_refresh_errors(self):
        for error in (AIAuthError("a"), AINotFoundError("n"), AINetworkError("x"),
                      NotImplementedError(), AIProviderError("p")):
            with self.assertRaises(UserError):
                self._refresh(error=error)
        with self.assertRaises(UserError):
            self._refresh(models=[])

    def test_refresh_needs_own_key(self):
        with self.assertRaises(UserError):
            self.claude.with_user(self.admin).action_refresh_models()


@tagged("post_install", "-at_install")
class TestDashboard(VibeCommon):

    def test_empty_dashboard(self):
        self.env["vibe.generated.module"].search([]).unlink()
        self.env["vibe.conversation"].search([]).unlink()
        dash = self.env["vibe.dashboard"].create({})
        self.assertEqual(dash.name, "Dashboard")
        self.assertEqual(dash.total_conversations, 0)
        self.assertEqual(dash.success_rate, 0.0)
        self.assertIn("No provider usage yet", dash.provider_breakdown_html)
        self.assertIn("No user activity yet", dash.top_users_html)
        self.assertIn("No module generation activity", dash.activity_sparkline_html)

    def test_dashboard_stats(self):
        self.env["vibe.generated.module"].search([]).unlink()
        self.env["vibe.conversation"].search([]).unlink()
        conv = self.env["vibe.conversation"].create({
            "user_id": self.user.id, "provider_config_id": self.config_gemini.id})
        self.env["vibe.message"].create({
            "conversation_id": conv.id, "role": "assistant", "content": "x",
            "tokens_input": 40, "tokens_output": 60, "tokens_used": 100,
        })
        valid = self._make_module(conversation=conv)
        valid.write({"validation_state": "valid", "download_count": 2})
        invalid = self._make_module(conversation=conv)
        invalid.validation_state = "invalid"

        dash = self.env["vibe.dashboard"].create({})
        self.assertEqual(dash.total_conversations, 1)
        self.assertEqual(dash.total_modules, 2)
        self.assertEqual(dash.total_tokens, 100)
        self.assertEqual(dash.total_users, 1)
        self.assertEqual(dash.total_downloads, 2)
        self.assertEqual((dash.valid_modules, dash.invalid_modules), (1, 1))
        self.assertAlmostEqual(dash.success_rate, 0.5)
        self.assertEqual(dash.avg_tokens_per_module, 50)
        self.assertEqual(dash.modules_last_24h, 2)
        self.assertIn("Google Gemini", dash.provider_breakdown_html)
        self.assertIn("vibe_user", dash.top_users_html)
        self.assertIn("<svg", dash.activity_sparkline_html)

    def test_dashboard_actions(self):
        dash_model = self.env["vibe.dashboard"]
        action = dash_model.action_open_dashboard()
        self.assertEqual(action["res_model"], "vibe.dashboard")
        dash = dash_model.browse(action["res_id"])
        self.assertEqual(dash.action_view_all_conversations()["res_model"], "vibe.conversation")
        self.assertEqual(dash.action_view_all_modules()["res_model"], "vibe.generated.module")
        self.assertEqual(dash.action_view_valid_modules()["domain"],
                         [("validation_state", "=", "valid")])
        self.assertEqual(dash.action_view_invalid_modules()["domain"],
                         [("validation_state", "=", "invalid")])


@tagged("post_install", "-at_install")
class TestExporter(VibeCommon):

    def test_export_contents(self):
        conv = self.env["vibe.conversation"].create({
            "user_id": self.user.id, "provider_config_id": self.config_gemini.id,
            "last_activity": "2026-01-01 10:00:00"})
        mod = self._make_module(conversation=conv)
        mod.validation_errors = json.dumps([{"file": "a", "line": 1, "message": "m"}])
        self.env["vibe.message"].create({
            "conversation_id": conv.id, "role": "assistant", "content": "done",
            "generated_module_id": mod.id})
        filename, data = build_export(conv)
        self.assertIn("product_brand", filename)
        export = json.loads(data)
        self.assertNotIn("test-key", data.decode())
        self.assertTrue(export)

    def test_export_tolerates_bad_json_and_no_module(self):
        conv = self.env["vibe.conversation"].create({"user_id": self.user.id})
        filename, data = build_export(conv)
        self.assertTrue(filename.endswith(".json"))
        mod = self._make_module(conversation=conv)
        mod.write({"manifest_data": "{bad", "validation_errors": "[bad"})
        _filename, data = build_export(conv)
        self.assertTrue(json.loads(data))
