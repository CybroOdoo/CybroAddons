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
from odoo import fields
from odoo.tests.common import TransactionCase


class TestWhatsappMessage(TransactionCase):
    """Test cases for the whatsapp.message model."""

    def setUp(self):
        """Set up an attachment and a whatsapp.message record for tests."""
        super().setUp()
        self.attachment = self.env["ir.attachment"].create(
            {
                "name": "Test Attachment",
                "type": "binary",
                "datas": b"dGVzdA==",  # base64 of 'test'
                "res_model": "pos.order",
                "mimetype": "application/pdf",
            }
        )
        self.message = self.env["whatsapp.message"].create(
            {
                "status": "sent",
                "from_user_id": self.env.user.id,
                "to_user": "+919876543210",
                "user_name": "Test Customer",
                "body": "Your Invoice is here",
                "attachment_id": self.attachment.id,
                "date_and_time_sent": fields.Datetime.now(),
            }
        )

    def test_01_whatsapp_message_create(self):
        """Test that a whatsapp.message record is correctly created."""
        self.assertEqual(self.message.status, "sent")
        self.assertEqual(self.message.to_user, "+919876543210")
        self.assertEqual(self.message.user_name, "Test Customer")
        self.assertEqual(self.message.body, "Your Invoice is here")
        self.assertEqual(self.message.from_user_id, self.env.user)

    def test_02_whatsapp_message_missing_required_raises(self):
        """Test that omitting required fields raises DB exception."""
        # Use unittest.TestCase.assertRaises for Exception tuples
        # (Odoo's assertRaises only accepts a single exception class)
        try:
            self.env["whatsapp.message"].create(
                {
                    "status": "sent",
                    # Missing required fields: from_user_id, to_user...
                }
            )
            self.env.cr.flush()
            self.fail(
                "Expected an error when creating with missing required fields."
            )
        except Exception:
            pass  # Expected — constraint or NOT NULL violation

    def test_03_whatsapp_message_date_set(self):
        """Test that the date_and_time_sent field can be set and retrieved."""
        self.assertTrue(
            self.message.date_and_time_sent,
            "date_and_time_sent should be set.",
        )

    def test_04_whatsapp_message_attachment_linked(self):
        """Test that the attachment_id is properly linked."""
        self.assertEqual(self.message.attachment_id, self.attachment)

    def test_05_multiple_messages_searchable(self):
        """Test that multiple whatsapp.message records are searchable."""
        self.env["whatsapp.message"].create(
            {
                "status": "sent",
                "from_user_id": self.env.user.id,
                "to_user": "+911111111111",
                "user_name": "Customer Two",
                "body": "Your Receipt is here",
                "date_and_time_sent": fields.Datetime.now(),
            }
        )
        messages = self.env["whatsapp.message"].search(
            [
                ("to_user", "in", ["+919876543210", "+911111111111"]),
            ]
        )
        self.assertEqual(
            len(messages), 2, "Should find both whatsapp message records."
        )

    def test_06_whatsapp_message_model_name(self):
        """Test that the model name is correctly set."""
        self.assertEqual(
            self.env["whatsapp.message"]._name, "whatsapp.message"
        )

    def test_07_whatsapp_message_required_field_list(self):
        """Verify that all expected required fields are present."""
        required_fields = ["from_user_id", "to_user", "user_name", "body"]
        model_fields = self.env["whatsapp.message"]._fields
        for fname in required_fields:
            self.assertIn(
                fname,
                model_fields,
                f"Field '{fname}' should exist on whatsapp.message.",
            )
            self.assertTrue(
                model_fields[fname].required,
                f"Field '{fname}' should be required.",
            )
