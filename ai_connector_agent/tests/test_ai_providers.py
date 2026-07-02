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

from .common import AIConnectorAgentTestCase, MockResponse


class TestAIProviders(AIConnectorAgentTestCase):
    def test_action_fetch_models_creates_and_links_records(self):
        existing_model_id = "gpt-4o-mini-provider-test"
        existing_model = self.env["ai.model"].create({
            "modelId": existing_model_id,
            "object": "model",
        })
        payload = {
            "data": [
                {"id": "gpt-4.1", "object": "model", "version": "2026-01"},
                {"id": existing_model_id, "object": "model"},
            ]
        }

        with patch("odoo.addons.ai_connector_agent.models.ai_providers.requests.get", return_value=MockResponse(payload=payload)) as mock_get:
            self.provider.action_fetch_models()

        self.assertEqual(mock_get.call_args.args[0], "https://api.openai.com/v1/models")
        self.assertEqual(mock_get.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")
        model_ids = self.provider.ai_model_ids.mapped("modelId")
        self.assertIn("gpt-4.1", model_ids)
        self.assertIn("gpt-4o-mini", model_ids)
        self.assertEqual(self.env["ai.model"].search_count([("modelId", "=", existing_model_id)]), 1)
        self.assertIn(existing_model, self.provider.ai_model_ids)

    def test_action_fetch_models_rejects_invalid_json_structure(self):
        with patch("odoo.addons.ai_connector_agent.models.ai_providers.requests.get", return_value=MockResponse(payload=["bad-data"])):
            with self.assertRaises(UserError):
                self.provider.action_fetch_models()
