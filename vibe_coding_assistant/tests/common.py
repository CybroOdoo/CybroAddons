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
from unittest.mock import MagicMock

from odoo.tests.common import TransactionCase

VALID_PAYLOAD = {
    "module": {
        "technical_name": "library_book",
        "display_name": "Library Book",
        "version": "20.0.1.0.0",
        "summary": "Manage library books",
        "depends": ["base"],
        "category": "Services",
        "license": "LGPL-3",
        "author": "Tester",
    },
    "files": [
        {"path": "__manifest__.py", "content": "{'name': 'Library Book'}\n"},
        {"path": "__init__.py", "content": "from . import models\n"},
        {"path": "models/__init__.py", "content": "\n"},
    ],
}
USAGE = {"input": 10, "output": 20, "total": 30}
BUILD_PROMPT = "Create a module to manage library books"


def valid_reply():
    return json.dumps(VALID_PAYLOAD), dict(USAGE)


def fake_provider(reply=None, error=None):
    """Return a MagicMock behaving like an AIProviderBase instance."""
    provider = MagicMock()
    if error is not None:
        provider.generate.side_effect = error
    else:
        provider.generate.return_value = reply or valid_reply()
    return provider


class VibeCommon(TransactionCase):
    """Shared fixtures: two Vibe Coders, one provider, one active config."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_coder = cls.env.ref("vibe_coding_assistant.group_vibe_coder")
        cls.user_a = cls._make_user("vibe_user_a")
        cls.user_b = cls._make_user("vibe_user_b")
        cls.provider = cls.env["ai.provider"].create({
            "name": "Test Provider",
            "code": "gemini_test",
            "default_model": "model-1",
            "available_models": "model-1\nmodel-2",
            "api_base_url": "https://example.invalid",
        })
        cls.provider_2 = cls.env["ai.provider"].create({
            "name": "Second Provider",
            "code": "claude_test",
            "default_model": "model-x",
            "available_models": "model-x",
            "api_base_url": "https://example.invalid",
        })
        cls.config_a = cls.env["ai.provider.user.config"].create({
            "user_id": cls.user_a.id,
            "provider_id": cls.provider.id,
            "api_key": "secret-a",
            "selected_model": "model-1",
            "is_active": True,
        })

    @classmethod
    def _make_user(cls, login):
        users = cls.env["res.users"]
        group_field = "group_ids" if "group_ids" in users._fields else "groups_id"
        return users.with_context(no_reset_password=True).create({
            "name": login,
            "login": login,
            "email": "%s@example.com" % login,
            "password": "vibe_pass_123456",
            group_field: [
                (6, 0, [cls.env.ref("base.group_user").id, cls.group_coder.id]),
            ],
        })

    def _make_conversation(self, user=None, **vals):
        values = {"name": "Chat", "user_id": (user or self.user_a).id}
        values.update(vals)
        return self.env["vibe.conversation"].create(values)

    def _make_module(self, conversation, **vals):
        values = {
            "conversation_id": conversation.id,
            "technical_name": "library_book",
            "name": "Library Book",
            "manifest_data": json.dumps(VALID_PAYLOAD["module"]),
        }
        values.update(vals)
        module = self.env["vibe.generated.module"].create(values)
        self.env["vibe.generated.file"].create([
            dict(module_id=module.id, **f) for f in VALID_PAYLOAD["files"]
        ])
        return module
