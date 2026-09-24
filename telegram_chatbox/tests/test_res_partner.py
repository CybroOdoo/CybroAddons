# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase

class TestResPartnerTelegram(TransactionCase):
    def test_telegram_fields_exist(self):
        """Verify that telegram integration fields exist in res.partner model."""
        partner = self.env["res.partner"].create({
            "name": "Emma Watson",
            "telegram_chat_id": "112233",
            "telegram_username": "emma_watson",
            "telegram_opt_in": True,
        })
        self.assertEqual(partner.telegram_chat_id, "112233")
        self.assertEqual(partner.telegram_username, "emma_watson")
        self.assertTrue(partner.telegram_opt_in)
