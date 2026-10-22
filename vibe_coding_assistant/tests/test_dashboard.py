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

from odoo.tests import tagged

from .common import VibeCommon

@tagged("post_install", "-at_install")
class TestDashboard(VibeCommon):

    def test_empty_dashboard_has_placeholders(self):
        dash = self.env["vibe.dashboard"].create({})
        self.assertEqual(dash.name, "Dashboard")
        self.assertIn("o_vibe_dash_empty_section", dash.activity_sparkline_html)

    def test_stats_with_data(self):
        conv = self._make_conversation(provider_config_id=self.config_a.id)
        self.env["vibe.message"].create({
            "conversation_id": conv.id, "role": "assistant", "content": "x",
            "tokens_input": 40, "tokens_output": 60, "tokens_used": 100,
        })
        self._make_module(conv, validation_state="valid", download_count=3)
        self._make_module(conv, validation_state="invalid")
        self._make_module(conv, validation_state="pending")
        before = self.env["vibe.dashboard"].create({})
        # Counts include any pre-existing data, so assert on the deltas we
        # can derive from the totals instead of absolute values.
        self.assertGreaterEqual(before.total_conversations, 1)
        self.assertGreaterEqual(before.total_modules, 3)
        self.assertGreaterEqual(before.valid_modules, 1)
        self.assertGreaterEqual(before.invalid_modules, 1)
        self.assertGreaterEqual(before.pending_modules, 1)
        self.assertGreaterEqual(before.total_downloads, 3)
        self.assertGreaterEqual(before.total_tokens, 100)
        self.assertEqual(before.total_tokens,
                         before.total_input_tokens + before.total_output_tokens)
        self.assertGreaterEqual(before.modules_last_24h, 3)
        self.assertGreaterEqual(before.modules_last_7d, 3)
        self.assertGreaterEqual(before.modules_last_30d, 3)
        self.assertTrue(0.0 < before.success_rate < 1.0)
        self.assertGreater(before.avg_tokens_per_module, 0)
        self.assertIn("Test Provider", before.provider_breakdown_html)
        self.assertIn("vibe_user_a", before.top_users_html)
        self.assertIn("<svg", before.activity_sparkline_html)

    def test_actions(self):
        Dash = self.env["vibe.dashboard"]
        opened = Dash.action_open_dashboard()
        self.assertEqual(opened["res_model"], "vibe.dashboard")
        dash = Dash.browse(opened["res_id"])
        self.assertEqual(dash.action_view_all_conversations()["res_model"],
                         "vibe.conversation")
        self.assertEqual(dash.action_view_all_modules()["res_model"],
                         "vibe.generated.module")
        self.assertEqual(dash.action_view_valid_modules()["domain"],
                         [("validation_state", "=", "valid")])
        self.assertEqual(dash.action_view_invalid_modules()["domain"],
                         [("validation_state", "=", "invalid")])
