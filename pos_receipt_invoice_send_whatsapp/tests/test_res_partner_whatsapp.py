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
from odoo.tests.common import TransactionCase


class TestResPartnerWhatsapp(TransactionCase):
    """Test cases for the res.partner WhatsApp number field."""

    def setUp(self):
        """Set up a partner with a WhatsApp number for tests."""
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "WhatsApp Test Partner",
                "whatsapp_number": "+911234567890",
            }
        )

    def test_01_partner_whatsapp_number_field_exists(self):
        """Test that the whatsapp_number field is added to res.partner."""
        self.assertIn(
            "whatsapp_number",
            self.env["res.partner"]._fields,
            "'whatsapp_number' field should exist on res.partner model.",
        )

    def test_02_partner_whatsapp_number_stored(self):
        """Test that the WhatsApp number is stored and retrievable."""
        self.assertEqual(self.partner.whatsapp_number, "+911234567890")

    def test_03_partner_whatsapp_number_can_be_updated(self):
        """Test that the WhatsApp number can be updated."""
        self.partner.whatsapp_number = "+919999999999"
        self.partner.flush_recordset()
        self.assertEqual(self.partner.whatsapp_number, "+919999999999")

    def test_04_partner_without_whatsapp_number(self):
        """Test that a partner can be created without a WhatsApp number."""
        partner_no_wa = self.env["res.partner"].create(
            {"name": "No WA Partner"}
        )
        self.assertFalse(
            partner_no_wa.whatsapp_number,
            "WhatsApp number should be empty/False by default.",
        )
