# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase


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

    def test_compute_global_service_charge(self):
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("all_in_one_pos_kit.enable_service_charge", "True")
        params.set_param("all_in_one_pos_kit.visibility", "session")
        params.set_param("all_in_one_pos_kit.global_selection", "percentage")
        params.set_param("all_in_one_pos_kit.global_charge", "7.5")
        params.set_param(
            "all_in_one_pos_kit.global_product_id",
            str(self.service_product.id),
        )

        self.pos_config._compute_global_service_charge()

        self.assertTrue(self.pos_config.enable_service_charge)
        self.assertEqual(self.pos_config.sc_visibility, "session")
        self.assertEqual(self.pos_config.global_selection, "percentage")
        self.assertEqual(self.pos_config.global_charge, 7.5)
        self.assertEqual(self.pos_config.global_product_id, self.service_product.id)

    def test_compute_is_session(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "all_in_one_pos_kit.visibility",
            "session",
        )

        self.pos_config._compute_is_session()

        self.assertTrue(self.pos_config.is_session)

    def test_onchange_service_charges_sets_and_clears_defaults(self):
        config = self.env["pos.config"].new({
            "name": "Onchange POS",
            "is_service_charges": True,
        })

        config._onchange_is_service_charges()
        self.assertTrue(config.service_product_id)
        self.assertEqual(config.service_charge, 10.0)

        config.is_service_charges = False
        config._onchange_is_service_charges()
        self.assertFalse(config.service_product_id)
        self.assertEqual(config.service_charge, 0.0)

    def test_compute_and_search_is_allowed_pos(self):
        self.env.user.pos_config_ids = [(6, 0, self.pos_config.ids)]

        self.pos_config._compute_is_allowed_pos()

        self.assertTrue(self.pos_config.is_allowed_pos)
        self.assertEqual(
            self.env["pos.config"]._search_is_allowed_pos("=", True),
            [("id", "in", self.pos_config.ids)],
        )

    def test_load_pos_data_injects_global_service_charge_fields(self):
        base_path = "odoo.addons.point_of_sale.models.pos_config.PosConfig._load_pos_data"
        with patch(base_path, return_value={"data": [{"id": self.pos_config.id}]}):
            result = self.pos_config._load_pos_data({})

        self.assertIn("enable_service_charge", result["data"][0])
        self.assertIn("global_charge", result["data"][0])
