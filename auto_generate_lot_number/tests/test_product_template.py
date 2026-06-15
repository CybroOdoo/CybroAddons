# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.params = cls.env["ir.config_parameter"].sudo()
        cls.product = cls.env["product.product"].create({
            "name": "Auto Lot Product",
            "is_storable": True,
            "tracking": "lot",
            "prefix": "PROD",
            "digits": 5,
        })
        cls.template = cls.product.product_tmpl_id

    def setUp(self):
        super().setUp()
        self.params.set_param(
            "auto_generate_lot_number.is_auto_generate", True
        )
        self.params.set_param(
            "auto_generate_lot_number.serial_number_type", "product"
        )
        self.params.set_param("auto_generate_lot_number.prefix", "GLB")
        self.params.set_param("auto_generate_lot_number.digits", 4)

    def test_onchange_digits_prefix_resets_number_next(self):
        self.template.number_next = 12

        self.template._onchange_digits_prefix()

        self.assertEqual(self.template.number_next, 0)

    def test_check_string_for_nine(self):
        self.assertTrue(self.template.check_string_for_nine("999"))
        self.assertFalse(self.template.check_string_for_nine("990"))

    def test_number_next_actual_uses_product_sequence_settings(self):
        self.template.write({
            "prefix": "LOT",
            "digits": 4,
            "number_next": 0,
        })

        lot_name = self.template._number_next_actual()

        self.assertEqual(lot_name, "LOT0001")
        self.assertEqual(self.template.number_next, 1)

    def test_number_next_actual_falls_back_to_global_settings(self):
        self.template.write({
            "prefix": False,
            "digits": 0,
            "number_next": 0,
        })

        lot_name = self.template._number_next_actual()

        self.assertEqual(lot_name, "GLB0001")
        self.assertEqual(self.template.number_next, 1)

    def test_compute_is_auto_generate_depends_on_config(self):
        self.template._compute_is_auto_generate()
        self.assertTrue(self.template.is_auto_generate)

        self.params.set_param(
            "auto_generate_lot_number.serial_number_type", "global"
        )
        self.template._compute_is_auto_generate()

        self.assertFalse(self.template.is_auto_generate)

    def test_write_resets_number_next_when_sequence_settings_change(self):
        self.template.number_next = 15

        self.template.write({"prefix": "NEW"})

        self.assertEqual(self.template.number_next, 0)

    def test_write_keeps_number_next_for_unrelated_updates(self):
        self.template.number_next = 15

        self.template.write({"name": "Auto Lot Product Updated"})

        self.assertEqual(self.template.number_next, 15)
