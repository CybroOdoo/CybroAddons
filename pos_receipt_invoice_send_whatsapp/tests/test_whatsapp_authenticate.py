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
import base64
from unittest.mock import patch
from unittest.mock import MagicMock
from odoo.tests.common import TransactionCase


class TestWhatsappAuthenticate(TransactionCase):
    """Test cases for the whatsapp.authenticate wizard."""

    def setUp(self):
        """Set up a config manager and authentication wizard for tests."""
        super().setUp()
        self.pos_config = self.env["pos.config"].create(
            {"name": "Auth Test POS"}
        )
        self.config_manager = self.env["configuration.manager"].create(
            {
                "instance": "auth_instance",
                "token": "auth_token",
                "config_id": self.pos_config.id,
                "state": "draft",
            }
        )
        self.wizard = self.env["whatsapp.authenticate"].create(
            {
                "configuration_manager_id": self.config_manager.id,
            }
        )

    def test_01_wizard_create_with_config_manager(self):
        """Test that the whatsapp.authenticate wizard is correctly created."""
        self.assertEqual(
            self.wizard.configuration_manager_id, self.config_manager
        )

    def test_02_wizard_qrcode_field_optional(self):
        """Test that the qrcode field is optional and defaults to False."""
        self.assertFalse(
            self.wizard.qrcode,
            "The qrcode field should default to False/empty.",
        )

    @patch("requests.request")
    def test_03_action_save_triggers_authenticate(self, mock_request):
        """Test action_save calls action_authenticate on config manager."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "{}"
        mock_resp.json.return_value = {
            "status": {"accountStatus": {"substatus": "connected"}},
        }
        mock_request.return_value = mock_resp
        self.wizard.action_save()
        self.assertEqual(
            self.config_manager.state,
            "verified",
            "action_save should authenticate and set state to 'verified'.",
        )

    def test_04_wizard_can_set_qrcode(self):
        """Test that a qrcode binary can be set on the wizard."""
        test_qr = base64.b64encode(b"fake_qr_image_bytes")
        self.wizard.qrcode = test_qr
        self.assertTrue(self.wizard.qrcode)
