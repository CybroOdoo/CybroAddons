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

from types import SimpleNamespace

from odoo.tests.common import TransactionCase


class MockResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class AIConnectorAgentTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provider = cls.env["ai.providers"].create({
            "name": "OpenAI",
            "api_key": "test-key",
            "api_base_url": "https://api.openai.com",
        })
        cls.model = cls.env["ai.model"].create({
            "modelId": "gpt-4o-mini",
            "object": "model",
        })
        cls.provider.ai_model_ids = [cls.model.id]
        cls.controller_patch_path = "odoo.addons.ai_connector_agent.controller.ai_connector_agent"

    def _controller(self):
        from odoo.addons.ai_connector_agent.controller.ai_connector_agent import AiChatController

        return AiChatController()

    def _request_stub(self):
        return SimpleNamespace(env=self.env)
