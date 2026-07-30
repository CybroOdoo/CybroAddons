# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPosKeyboardShortcut(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env["pos.config"].create({"name": "Shortcut POS"})

    def test_create_assigns_sequence_name(self):
        shortcut = self.env["pos.keyboard.shortcut"].create({})

        self.assertTrue(shortcut.name.startswith("PKS"))

    def test_constraint_rejects_duplicate_shortcut_keys(self):
        with self.assertRaises(ValidationError):
            self.env["pos.keyboard.shortcut"].create({
                "customer_screen": "A",
                "next_screen": "A",
            })

    def test_load_pos_data_domain_uses_selected_shortcut(self):
        shortcut = self.env["pos.keyboard.shortcut"].create({})
        self.pos_config.select_shortcut_id = shortcut
        data = {"pos.config": {"data": [{"id": self.pos_config.id}]}}

        domain = self.env["pos.keyboard.shortcut"]._load_pos_data_domain(data)

        self.assertEqual(domain, [("id", "=", shortcut.id)])

    def test_load_pos_data_domain_returns_false_when_no_shortcut_selected(self):
        self.pos_config.select_shortcut_id = False
        data = {"pos.config": {"data": [{"id": self.pos_config.id}]}}

        domain = self.env["pos.keyboard.shortcut"]._load_pos_data_domain(data)

        self.assertEqual(domain, [("id", "=", False)])

    def test_load_pos_data_fields_returns_expected_fields(self):
        fields_list = self.env["pos.keyboard.shortcut"]._load_pos_data_fields(
            self.pos_config.id
        )

        self.assertIn("customer_screen", fields_list)
        self.assertIn("validate_order", fields_list)
        self.assertIn("sent_email", fields_list)
