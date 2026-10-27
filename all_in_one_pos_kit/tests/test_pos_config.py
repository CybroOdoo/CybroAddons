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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service_product = cls.env["product.product"].create({
            "name": "Service Charge Product",
            "available_in_pos": True,
            "sale_ok": True,
            "type": "service",
        })
        cls.payment_method = cls.env["pos.payment.method"].create({
            "name": "Config Test Payment",
        })
        cls.pos_config = cls.env["pos.config"].create({
            "name": "Config Test POS",
            "payment_method_ids": [(6, 0, cls.payment_method.ids)],
        })


    def test_compute_is_session(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "all_in_one_pos_kit.visibility",
            "session",
        )

        self.pos_config._compute_is_session()

        self.assertTrue(self.pos_config.is_session)


    def test_compute_and_search_is_allowed_pos(self):
        self.env.user.pos_config_ids = [(6, 0, self.pos_config.ids)]

        self.pos_config._compute_is_allowed_pos()

        self.assertTrue(self.pos_config.is_allowed_pos)
        self.assertEqual(
            self.env["pos.config"]._search_is_allowed_pos("=", True),
            [("id", "in", self.pos_config.ids)],
        )

    def test_load_pos_data_fields_include_service_charge_fields(self):
        fields_list = self.env["pos.config"]._load_pos_data_fields(self.pos_config)
        if fields_list:
            self.assertIn("is_service_charges", fields_list)
            self.assertIn("service_charge", fields_list)
            self.assertIn("service_product_id", fields_list)
