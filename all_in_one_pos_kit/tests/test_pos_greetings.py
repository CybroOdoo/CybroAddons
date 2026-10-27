# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase, tagged

REQUESTS_POST = (
    "odoo.addons.all_in_one_pos_kit.models.pos_greetings.requests.post")


@tagged('post_install', '-at_install')
class TestPosGreetings(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Greeted"})
        cls.greeting = cls.env["pos.greetings"].create({
            "customer_id": cls.partner.id,
            "to_number": "+10000000001",
            "twilio_number": "+10000000002",
            "sms_body": "Thank you for shopping with us",
        })

    def test_greeting_not_sent_without_credentials(self):
        with patch(REQUESTS_POST) as post:
            self.greeting.action_send_greeting()
        post.assert_not_called()
        self.assertFalse(self.greeting.send_sms)

    def test_greeting_sent_with_credentials(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("all_in_one_pos_kit.account_sid", "AC123")
        params.set_param("all_in_one_pos_kit.twilio_auth_token", "token")
        with patch(REQUESTS_POST, return_value=MagicMock()) as post:
            self.greeting.action_send_greeting()
        post.assert_called_once()
        self.assertTrue(self.greeting.send_sms)

    def test_no_greeting_created_when_disabled(self):
        order = self.env["pos.order"].new({"partner_id": self.partner.id})
        before = self.env["pos.greetings"].search_count([])
        order._create_and_send_greetings()
        self.assertEqual(self.env["pos.greetings"].search_count([]), before)
