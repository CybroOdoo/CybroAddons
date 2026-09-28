# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024 TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Akhil(<https://www.cybrosys.com>)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.mandatory_field_highlight.controllers.mandatory_field_highlight import (
    MandatoryFieldSettings,
)


@tagged("post_install", "-at_install")
class TestMandatoryFieldHighlight(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["ir.config_parameter"].sudo()
        cls.settings_model = cls.env["res.config.settings"]
        cls.expected_values = {
            "margin_left_color": "#111111",
            "margin_right_color": "#222222",
            "margin_top_color": "#333333",
            "margin_bottom_color": "#444444",
            "field_background_color": "#555555",
        }

    def test_set_values_persists_all_color_configuration(self):
        settings = self.settings_model.create(self.expected_values)

        settings.set_values()

        self.assertEqual(
            self.config.get_param("mandatory_field_highlight.margin_left_color"),
            "#111111",
        )
        self.assertEqual(
            self.config.get_param("mandatory_field_highlight.margin_right_color"),
            "#222222",
        )
        self.assertEqual(
            self.config.get_param("mandatory_field_highlight.margin_top_color"),
            "#333333",
        )
        self.assertEqual(
            self.config.get_param("mandatory_field_highlight.margin_bottom_color"),
            "#444444",
        )
        self.assertEqual(
            self.config.get_param(
                "mandatory_field_highlight.field_background_color"
            ),
            "#555555",
        )

    def test_get_values_reads_saved_configuration(self):
        for key, value in self.expected_values.items():
            self.config.set_param(f"mandatory_field_highlight.{key}", value)

        values = self.settings_model.get_values()

        self.assertEqual(values["margin_left_color"], "#111111")
        self.assertEqual(values["margin_right_color"], "#222222")
        self.assertEqual(values["margin_top_color"], "#333333")
        self.assertEqual(values["margin_bottom_color"], "#444444")
        self.assertEqual(values["field_background_color"], "#555555")

    def test_controller_returns_saved_color_configuration(self):
        for key, value in self.expected_values.items():
            self.config.set_param(f"mandatory_field_highlight.{key}", value)
        fake_request = SimpleNamespace(env=self.env)

        with patch(
            "odoo.addons.mandatory_field_highlight.controllers.mandatory_field_highlight.request",
            fake_request,
        ), patch("odoo.http.request", fake_request):
            result = MandatoryFieldSettings().website_get_config_value()

        self.assertEqual(result, self.expected_values)
