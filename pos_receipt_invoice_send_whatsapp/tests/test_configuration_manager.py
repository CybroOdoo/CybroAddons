# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Arjun P P (odoo@cybrosys.com)
#
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
###############################################################################
import json
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestConfigurationManager(TransactionCase):
    """Test cases for the configuration.manager model."""

    def setUp(self):
        """Set up a POS config and a configuration.manager record for tests."""
        super().setUp()
        self.pos_config = self.env["pos.config"].create(
            {"name": "Test POS Config"}
        )
        self.config_manager = self.env["configuration.manager"].create(
            {
                "instance": "test_instance_123",
                "token": "test_token_abc",
                "config_id": self.pos_config.id,
            }
        )

    def test_01_configuration_manager_create(self):
        """Test configuration.manager record creation with required fields."""
        self.assertEqual(self.config_manager.instance, "test_instance_123")
        self.assertEqual(self.config_manager.token, "test_token_abc")
        self.assertEqual(self.config_manager.config_id, self.pos_config)
        self.assertEqual(
            self.config_manager.state,
            "draft",
            "Default state should be 'draft'",
        )

    def test_02_configuration_manager_default_state(self):
        """Test that the default state for configuration manager is 'draft'."""
        self.assertEqual(self.config_manager.state, "draft")

    def test_03_display_notification_success(self):
        """Test display_notification returns correct action for success."""
        result = self.config_manager.display_notification(
            "success", "Connected!"
        )
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(result["tag"], "display_notification")
        self.assertEqual(result["params"]["message"], "Connected!")
        self.assertEqual(result["params"]["type"], "success")
        self.assertFalse(result["params"]["sticky"])

    def test_04_display_notification_danger(self):
        """Test display_notification returns correct action for danger."""
        result = self.config_manager.display_notification("danger", "Error!")
        self.assertEqual(result["params"]["type"], "danger")
        self.assertEqual(result["params"]["message"], "Error!")

    @patch("requests.request")
    def test_05_action_authenticate_invalid_token(self, mock_request):
        """Test ValidationError raised for a non-200 API status response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_request.return_value = mock_resp
        with self.assertRaises(ValidationError):
            self.config_manager.action_authenticate()

    @patch("requests.request")
    def test_06_action_authenticate_already_connected(self, mock_request):
        """Test state becomes 'verified' when API returns 'connected'."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"status": "ok"}'
        mock_resp.json.return_value = {
            "status": {
                "accountStatus": {"substatus": "connected"},
            },
        }
        mock_request.return_value = mock_resp
        result = self.config_manager.action_authenticate()
        self.assertEqual(self.config_manager.state, "verified")
        self.assertEqual(result["params"]["message"], "Already connected")

    @patch("requests.get")
    @patch("requests.request")
    def test_07_action_authenticate_qr_flow(self, mock_request, mock_get):
        """Test that the QR wizard is opened when status is 'normal'."""
        mock_status_resp = MagicMock()
        mock_status_resp.status_code = 200
        mock_status_resp.text = '{"status": "ok"}'
        mock_status_resp.json.return_value = {
            "status": {"accountStatus": {"substatus": "normal"}},
        }
        mock_request.return_value = mock_status_resp

        mock_qr_resp = MagicMock()
        mock_qr_resp.status_code = 200
        mock_qr_resp.text = '{"qrCode": "some_qr_data_string"}'
        mock_get.return_value = mock_qr_resp

        result = self.config_manager.action_authenticate()
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "whatsapp.authenticate")

    @patch("requests.get")
    def test_08_get_qr_code_success(self, mock_get):
        """Test get_qr_code returns QR string on HTTP 200."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"qrCode": "abc123"}'
        mock_get.return_value = mock_resp
        result = self.config_manager.get_qr_code()
        self.assertEqual(result, '{"qrCode": "abc123"}')

    @patch("requests.get")
    def test_09_get_qr_code_failure(self, mock_get):
        """Test get_qr_code returns None on non-200 response."""
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp
        result = self.config_manager.get_qr_code()
        self.assertIsNone(result)

    def test_10_open_authenticate_wizard(self):
        """Test that open_authenticate_wizard returns correct window action."""
        qr_code_string = "test_qr_code_data"
        qr_code_data = json.dumps({"qrCode": qr_code_string})
        result = self.config_manager.open_authenticate_wizard(qr_code_data)
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "whatsapp.authenticate")
        self.assertIn("default_qrcode", result["context"])
        self.assertEqual(
            result["context"]["default_configuration_manager_id"],
            self.config_manager.id,
        )
