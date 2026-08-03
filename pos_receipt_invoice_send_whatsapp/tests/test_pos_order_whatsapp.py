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
import requests
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase


class TestPosOrderWhatsapp(TransactionCase):
    """Test cases for the PosOrder WhatsApp integration methods."""

    def setUp(self):
        """Set up a POS config, partner and verified API configuration."""
        super().setUp()
        self.pos_config = self.env["pos.config"].create({"name": "Test POS"})
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "whatsapp_number": "+919876543210",
            }
        )
        self.config_manager = self.env["configuration.manager"].create(
            {
                "instance": "test_instance",
                "token": "test_token",
                "config_id": self.pos_config.id,
                "state": "verified",
            }
        )

    def _open_session_and_create_order(self):
        """Helper: open a POS session and create a minimal POS order.

        pos.order does not require lines — we create a bare order so we can
        test the WhatsApp send methods without needing to create a product
        (blocked by website_sale publish_date NOT NULL constraint).
        """
        self.pos_config.open_ui()
        session = self.pos_config.current_session_id
        order = self.env["pos.order"].create(
            {
                "company_id": self.env.company.id,
                "session_id": session.id,
                "partner_id": self.partner.id,
                "amount_tax": 0.0,
                "amount_total": 0.0,
                "amount_paid": 0.0,
                "amount_return": 0.0,
            }
        )
        return order, session

    def test_01_get_instance_with_verified_config(self):
        """Test get_instance returns valid instant_id for verified config."""
        order = self.env["pos.order"]
        result = order.get_instance(config_id=self.pos_config.id)
        self.assertIn("instant_id", result)
        self.assertEqual(result["instant_id"], self.config_manager.id)

    def test_02_get_instance_no_verified_config(self):
        """Test that get_instance returns 0 when no verified config exists."""
        self.config_manager.state = "draft"
        order = self.env["pos.order"]
        result = order.get_instance(config_id=self.pos_config.id)
        self.assertEqual(
            result["instant_id"],
            0,
            "Should return empty id when no verified config exists.",
        )

    @patch("requests.post")
    def test_03_action_send_receipt_no_whatsapp_api(self, mock_post):
        """Test action_send_receipt error if no verified API config exists."""
        self.config_manager.state = "draft"
        order, session = self._open_session_and_create_order()
        result = order.action_send_receipt(
            name=order.name,
            partner={
                "whatsapp": "+919876543210",
                "name": "Test Partner",
                "config_id": self.pos_config.id,
            },
            ticket=base64.b64encode(b"fake_receipt_image_data"),
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("not connected", result["message"].lower())

    @patch("requests.post")
    def test_04_action_send_receipt_no_whatsapp_number(self, mock_post):
        """Test action_send_receipt error if partner has no WhatsApp number."""
        order, session = self._open_session_and_create_order()
        result = order.action_send_receipt(
            name=order.name,
            partner={
                "whatsapp": "",
                "name": "Test Partner",
                "config_id": self.pos_config.id,
            },
            ticket=base64.b64encode(b"fake_receipt_image_data"),
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("whatsapp number", result["message"].lower())

    @patch("requests.post")
    def test_05_action_send_receipt_success(self, mock_post):
        """Test action_send_receipt sends and logs WhatsApp message."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        order, session = self._open_session_and_create_order()
        ticket_data = base64.b64encode(b"fake_receipt_image_data")
        order.action_send_receipt(
            name=order.name,
            partner={
                "whatsapp": "+919876543210",
                "name": "Test Partner",
                "config_id": self.pos_config.id,
            },
            ticket=ticket_data,
        )
        message_log = self.env["whatsapp.message"].search(
            [
                ("to_user", "=", "+919876543210"),
                ("body", "=", "Your Receipt is here"),
            ],
            limit=1,
        )
        self.assertTrue(
            message_log, "A WhatsApp message log should be created on success."
        )

    @patch("requests.post")
    def test_06_action_send_receipt_request_exception(self, mock_post):
        """Test action_send_receipt error on requests.RequestException."""

        mock_post.side_effect = requests.RequestException(
            "Connection timed out"
        )
        order, session = self._open_session_and_create_order()
        result = order.action_send_receipt(
            name=order.name,
            partner={
                "whatsapp": "+919876543210",
                "name": "Test Partner",
                "config_id": self.pos_config.id,
            },
            ticket=base64.b64encode(b"fake_data"),
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("Connection timed out", result["message"])
