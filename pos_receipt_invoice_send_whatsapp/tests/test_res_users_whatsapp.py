# -*- coding: utf-8 -*-
################################################################################
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
from odoo import fields as odoo_fields
from odoo.tests.common import TransactionCase


class TestResUsersWhatsapp(TransactionCase):
    """Test cases for the res.users WhatsApp group check field."""

    def setUp(self):
        """Set up the current user reference for tests."""
        super().setUp()
        self.user = self.env.user

    def test_01_whatsapp_groups_checks_field_exists(self):
        """Test 'whatsapp_groups_checks' computed field exists on res.users."""
        self.assertIn(
            "whatsapp_groups_checks",
            self.env["res.users"]._fields,
            "'whatsapp_groups_checks' should be on the res.users model.",
        )

    def test_02_whatsapp_groups_checks_is_boolean_field(self):
        """Test that 'whatsapp_groups_checks' is defined as a Boolean field."""
        field = self.env["res.users"]._fields.get("whatsapp_groups_checks")
        self.assertIsNotNone(field)
        self.assertIsInstance(
            field,
            odoo_fields.Boolean,
            "'whatsapp_groups_checks' must be a Boolean field.",
        )

    def test_03_whatsapp_groups_checks_is_computed(self):
        """Test that the field has a compute method defined."""
        field = self.env["res.users"]._fields.get("whatsapp_groups_checks")
        self.assertIsNotNone(field)
        self.assertTrue(
            field.compute,
            "'whatsapp_groups_checks' should be a computed field.",
        )
        self.assertEqual(
            field.compute,
            "_compute_pos_receipt_invoice_send_whatsapp_group_user",
        )

    def test_04_whatsapp_groups_checks_compute_method_exists(self):
        """Test the compute method is defined on the model."""
        self.assertTrue(
            hasattr(
                type(self.env["res.users"]),
                "_compute_pos_receipt_invoice_send_whatsapp_group_user",
            ),
            "The compute method must exist on res.users model.",
        )

    def test_05_non_group_user_creation(self):
        """Test user creation without WhatsApp group membership."""
        new_user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Plain WA Test User",
                    "login": "plain_user_wa_test_unique@test.com",
                    "email": "plain_user_wa_test_unique@test.com",
                }
            )
        )
        # Verify we can read field description (no trigger compute)
        self.assertIn(
            "whatsapp_groups_checks",
            type(new_user)._fields,
            "New user should still expose the 'whatsapp_groups_checks' field.",
        )
