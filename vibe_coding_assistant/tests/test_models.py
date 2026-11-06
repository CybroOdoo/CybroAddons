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
"""ORM, security and controller tests for the Vibe Coding Assistant.

The AI provider is always mocked — these tests never touch the network.
"""
import io
import json
import zipfile
from unittest.mock import MagicMock, patch

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger

from ..hooks import LATEST_MODELS, refresh_provider_models
from ..services.module_packager import build_zip
from ..services.provider_base import AIProviderError
from .test_services import _envelope

PROVIDER_PATH = (
    "odoo.addons.vibe_coding_assistant.models.vibe_conversation.get_provider"
)


class VibeCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login="vibe_user", groups="base.group_user")
        cls.other_user = new_test_user(cls.env, login="vibe_other", groups="base.group_user")
        cls.gemini = cls.env.ref("vibe_coding_assistant.provider_gemini")
        cls.claude = cls.env.ref("vibe_coding_assistant.provider_claude")
        Config = cls.env["ai.provider.user.config"]
        cls.config_gemini = Config.create({
            "user_id": cls.user.id,
            "provider_id": cls.gemini.id,
            "api_key": "test-key",
            "selected_model": "gemini-2.5-flash",
            "is_active": True,
        })
        cls.config_claude = Config.create({
            "user_id": cls.user.id,
            "provider_id": cls.claude.id,
            "api_key": "test-key",
            "selected_model": "claude-sonnet-4-5",
        })

    def _make_module(self, conversation=None, files=None):
        conversation = conversation or self.env["vibe.conversation"].create(
            {"user_id": self.user.id})
        parsed = _envelope()
        mod = self.env["vibe.generated.module"].create({
            "conversation_id": conversation.id,
            "technical_name": "product_brand",
            "name": "Product Brand",
            "manifest_data": json.dumps(parsed["module"]),
        })
        self.env["vibe.generated.file"].create([
            {"module_id": mod.id, "path": f["path"], "content": f["content"]}
            for f in (files or parsed["files"])
        ])
        return mod

    @staticmethod
    def _mock_provider(raw=None, usage=None, error=None):
        provider = MagicMock()
        if error:
            provider.generate.side_effect = error
        else:
            provider.generate.return_value = (
                raw, usage or {"input": 10, "output": 20, "total": 30})
        return provider


@tagged("post_install", "-at_install")
class TestProviders(VibeCommon):

    def test_seeded_providers(self):
        codes = set(self.env["ai.provider"].search([]).mapped("code"))
        self.assertTrue({"gemini", "claude", "openai"} <= codes)

    def test_single_default_provider(self):
        self.assertTrue(self.gemini.is_default)
        with self.assertRaises(ValidationError):
            self.claude.is_default = True

    def test_post_init_hook_refreshes_models(self):
        self.claude.available_models = "old-model"
        refresh_provider_models(self.env)
        self.assertEqual(self.claude.available_models, "\n".join(LATEST_MODELS["claude"]))


@tagged("post_install", "-at_install")
class TestUserConfig(VibeCommon):

    def test_activation_is_exclusive(self):
        Config = self.env["ai.provider.user.config"].with_user(self.user)
        self.assertEqual(Config.get_active_config_for_user(), self.config_gemini)
        self.config_claude.with_user(self.user).action_activate()
        self.assertTrue(self.config_claude.is_active)
        self.assertFalse(self.config_gemini.is_active)
        info = Config.get_active_provider_info()
        self.assertEqual(info["provider_code"], "claude")
        self.assertEqual(info["model"], "claude-sonnet-4-5")

    def test_name_compute(self):
        self.assertEqual(self.config_gemini.name, "%s (gemini-2.5-flash)" % self.gemini.name)

    def test_unique_per_user_provider(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(Exception):
            with self.env.cr.savepoint():
                self.env["ai.provider.user.config"].create({
                    "user_id": self.user.id,
                    "provider_id": self.gemini.id,
                    "api_key": "dup",
                    "selected_model": "x",
                })

    def test_configs_are_private(self):
        Config = self.env["ai.provider.user.config"].with_user(self.other_user)
        self.assertFalse(Config.search([]))
        self.assertFalse(Config.get_active_config_for_user())


@tagged("post_install", "-at_install")
class TestGeneratedModule(VibeCommon):

    def test_fields_registered(self):
        Module = self.env["vibe.generated.module"]
        self.assertIn("file_ids", Module._fields)
        self.assertIn("message_id", Module._fields)

    def test_technical_name_constraint(self):
        conv = self.env["vibe.conversation"].create({"user_id": self.user.id})
        with self.assertRaises(ValidationError):
            self.env["vibe.generated.module"].create({
                "conversation_id": conv.id,
                "technical_name": "Bad Name",
                "name": "Bad",
            })

    def test_language_compute_and_validation_errors(self):
        mod = self._make_module()
        languages = dict(mod.file_ids.mapped(lambda f: (f.path, f.language)))
        self.assertEqual(languages["models/product_brand.py"], "python")
        self.assertEqual(languages["security/ir.model.access.csv"], "csv")
        self.assertEqual(mod.get_validation_errors_list(), [])
        mod.validation_errors = "not json"
        self.assertEqual(mod.get_validation_errors_list(), [])

    def test_save_content_revalidates(self):
        mod = self._make_module()
        py_file = mod.file_ids.filtered(lambda f: f.path == "models/product_brand.py")
        result = py_file.save_content("def broken(:\n")
        self.assertTrue(py_file.user_modified)
        self.assertEqual(result["validation_state"], "invalid")
        self.assertEqual(mod.validation_state, "invalid")
        result = py_file.save_content("x = 1\n")
        self.assertEqual(result["validation_state"], "valid")
        with self.assertRaises(UserError):
            py_file.save_content(None)

    def test_build_zip(self):
        mod = self._make_module()
        with zipfile.ZipFile(io.BytesIO(build_zip(mod))) as zf:
            names = set(zf.namelist())
            self.assertIn("product_brand/__manifest__.py", names)
            self.assertIn("product_brand/models/product_brand.py", names)
            self.assertEqual(len(names), len(mod.file_ids))

    def test_generated_data_is_private(self):
        mod = self._make_module()
        Module = self.env["vibe.generated.module"].with_user(self.other_user)
        self.assertFalse(Module.search([("id", "=", mod.id)]))
        with self.assertRaises(AccessError):
            mod.with_user(self.other_user).read(["name"])


@tagged("post_install", "-at_install")
class TestConversation(VibeCommon):

    def setUp(self):
        super().setUp()
        self.conv = self.env["vibe.conversation"].with_user(self.user).create({})

    def test_empty_message_rejected(self):
        with self.assertRaises(UserError):
            self.conv.action_send_message("   ")

    def test_no_active_config(self):
        self.config_gemini.is_active = False
        with self.assertRaises(UserError):
            self.conv.action_send_message("Make a module")

    def test_send_message_success(self):
        provider = self._mock_provider(raw=json.dumps(_envelope()))
        with patch(PROVIDER_PATH, return_value=provider) as get_provider:
            payload = self.conv.action_send_message("Create a product brand module")
        get_provider.assert_called_once()
        self.assertEqual(get_provider.call_args.args[0], "gemini")

        self.assertEqual(self.conv.state, "active")
        self.assertEqual(self.conv.name, "Create a product brand module")
        self.assertEqual(self.conv.provider_config_id, self.config_gemini)
        self.assertEqual(self.conv.tokens_total, 30)

        mod = self.conv.generated_module_ids
        self.assertEqual(len(mod), 1)
        self.assertEqual(mod.validation_state, "valid")
        self.assertTrue(mod.message_id)
        self.assertIn("README.md", mod.file_ids.mapped("path"))

        roles = [m["role"] for m in payload["messages"]]
        self.assertEqual(roles, ["user", "assistant"])
        self.assertEqual(payload["messages"][1]["generated_module_id"], mod.id)
        self.assertEqual(payload["messages"][1]["generated_module_version"], "18.0.1.0.0")
        self.assertTrue(payload["conversation"]["can_refine"])

    def test_send_message_provider_error(self):
        provider = self._mock_provider(error=AIProviderError("quota exceeded"))
        with patch(PROVIDER_PATH, return_value=provider), \
                mute_logger("odoo.addons.vibe_coding_assistant.models.vibe_conversation"):
            payload = self.conv.action_send_message("Make a module")
        self.assertFalse(self.conv.generated_module_ids)
        self.assertIn("quota exceeded", payload["messages"][-1]["content"])

    def test_send_message_unparseable_response(self):
        provider = self._mock_provider(raw="Sorry, no JSON today.")
        with patch(PROVIDER_PATH, return_value=provider), \
                mute_logger("odoo.addons.vibe_coding_assistant.models.vibe_conversation"):
            payload = self.conv.action_send_message("Make a module")
        self.assertFalse(self.conv.generated_module_ids)
        self.assertEqual(payload["messages"][-1]["role"], "assistant")
        self.assertFalse(payload["conversation"]["can_refine"])

    def test_archive_and_export_action(self):
        self.conv.action_archive()
        self.assertEqual(self.conv.state, "archived")
        action = self.conv.action_export_json()
        self.assertEqual(action["url"], "/vibe/conversation/%d/export" % self.conv.id)

    def test_conversations_are_private(self):
        Conv = self.env["vibe.conversation"].with_user(self.other_user)
        self.assertFalse(Conv.search([("id", "=", self.conv.id)]))


@tagged("post_install", "-at_install")
class TestControllers(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login="vibe_http", password="vibe_http_pwd",
                                 groups="base.group_user")
        new_test_user(cls.env, login="vibe_http_other", password="vibe_http_other_pwd",
                      groups="base.group_user")
        cls.conv = cls.env["vibe.conversation"].create({"user_id": cls.user.id})
        parsed = _envelope()
        cls.module = cls.env["vibe.generated.module"].create({
            "conversation_id": cls.conv.id,
            "technical_name": "product_brand",
            "name": "Product Brand",
            "manifest_data": json.dumps(parsed["module"]),
        })
        cls.env["vibe.generated.file"].create([
            {"module_id": cls.module.id, "path": f["path"], "content": f["content"]}
            for f in parsed["files"]
        ])

    def test_download_zip(self):
        self.authenticate("vibe_http", "vibe_http_pwd")
        res = self.url_open("/vibe/module/%d/download" % self.module.id)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["Content-Type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(res.content)) as zf:
            self.assertIn("product_brand/__manifest__.py", zf.namelist())
        self.assertEqual(self.module.download_count, 1)

    def test_download_missing_module(self):
        self.authenticate("vibe_http", "vibe_http_pwd")
        res = self.url_open("/vibe/module/999999999/download")
        self.assertEqual(res.status_code, 404)

    @mute_logger("odoo.http")
    def test_download_other_users_module_denied(self):
        self.authenticate("vibe_http_other", "vibe_http_other_pwd")
        res = self.url_open("/vibe/module/%d/download" % self.module.id)
        self.assertNotEqual(res.status_code, 200)
        self.assertEqual(self.module.download_count, 0)

    def test_export_conversation(self):
        self.authenticate("vibe_http", "vibe_http_pwd")
        res = self.url_open("/vibe/conversation/%d/export" % self.conv.id)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(json.loads(res.content), dict)
