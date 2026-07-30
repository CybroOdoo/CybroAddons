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

from odoo.tests.common import TransactionCase


class TestPosPaymentMethodKey(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env["pos.config"].create({"name": "Shortcut POS"})
        cls.shortcut = cls.env["pos.keyboard.shortcut"].create({})
        cls.payment_method = cls.pos_config.payment_method_ids[:1]
        cls.payment_key = cls.env["pos.payment.method.key"].create({
            "payment_method_id": cls.payment_method.id,
            "keyboard_shortcut_id": cls.shortcut.id,
            "key_code": "1",
        })

    def test_load_pos_data_domain_uses_selected_shortcut(self):
        self.pos_config.select_shortcut_id = self.shortcut
        data = {"pos.config": {"data": [{"id": self.pos_config.id}]}}

        domain = self.env["pos.payment.method.key"]._load_pos_data_domain(data)

        self.assertEqual(domain, [("keyboard_shortcut_id", "=", self.shortcut.id)])

    def test_load_pos_data_domain_returns_false_when_no_shortcut_selected(self):
        self.pos_config.select_shortcut_id = False
        data = {"pos.config": {"data": [{"id": self.pos_config.id}]}}

        domain = self.env["pos.payment.method.key"]._load_pos_data_domain(data)

        self.assertEqual(domain, [("id", "=", False)])

    def test_load_pos_data_fields_returns_expected_fields(self):
        fields_list = self.env["pos.payment.method.key"]._load_pos_data_fields(
            self.pos_config.id
        )

        self.assertEqual(
            fields_list,
            ["id", "payment_method_id", "keyboard_shortcut_id", "key_code"],
        )
