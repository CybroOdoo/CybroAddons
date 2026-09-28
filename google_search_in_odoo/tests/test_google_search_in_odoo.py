# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil (odoo@cybrosys.com)
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
from unittest.mock import Mock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestGoogleSearchInOdoo(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["ir.config_parameter"].sudo()
        cls.settings = cls.env["res.config.settings"]

    def test_google_search_config_returns_error_when_disabled(self):
        self.config.set_param("google_search_in_odoo.google_search", False)
        self.config.set_param("google_search_in_odoo.ser_client_api", "api-key")
        self.config.set_param("google_search_in_odoo.ser_client_engine", "engine-id")

        result = self.settings.google_search_config("odoo")

        self.assertEqual(result, {"error": "Please enable Google Search."})

    def test_google_search_config_requires_both_credentials(self):
        self.config.set_param("google_search_in_odoo.google_search", True)
        self.config.set_param("google_search_in_odoo.ser_client_api", False)
        self.config.set_param("google_search_in_odoo.ser_client_engine", False)

        result = self.settings.google_search_config("odoo")

        self.assertEqual(
            result,
            {"error": "Please provide API key and Search engine ID."},
        )

    def test_google_search_config_returns_search_items(self):
        self.config.set_param("google_search_in_odoo.google_search", True)
        self.config.set_param("google_search_in_odoo.ser_client_api", "api-key")
        self.config.set_param("google_search_in_odoo.ser_client_engine", "engine-id")
        response = Mock(status_code=200)
        response.json.return_value = {
            "items": [
                {
                    "title": "Odoo",
                    "link": "https://www.odoo.com",
                    "snippet": "Business management software.",
                }
            ]
        }

        with patch(
            "odoo.addons.google_search_in_odoo.models.res_config_settings.requests.get",
            return_value=response,
        ) as get_mock:
            result = self.settings.google_search_config("odoo")

        get_mock.assert_called_once_with(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "q": "odoo",
                "key": "api-key",
                "cx": "engine-id",
                "num": 10,
            },
        )
        self.assertEqual(
            result,
            [
                {
                    "title": "Odoo",
                    "link": "https://www.odoo.com",
                    "snippet": "Business management software.",
                }
            ],
        )

    def test_google_search_config_returns_none_on_failed_response(self):
        self.config.set_param("google_search_in_odoo.google_search", True)
        self.config.set_param("google_search_in_odoo.ser_client_api", "api-key")
        self.config.set_param("google_search_in_odoo.ser_client_engine", "engine-id")
        response = Mock(status_code=403)

        with patch(
            "odoo.addons.google_search_in_odoo.models.res_config_settings.requests.get",
            return_value=response,
        ):
            result = self.settings.google_search_config("odoo")

        self.assertIsNone(result)
