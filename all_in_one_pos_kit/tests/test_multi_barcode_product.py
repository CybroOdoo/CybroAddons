# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestMultiBarcodeProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create({
            "name": "Multi Barcode Product",
            "available_in_pos": True,
        })

    def test_load_pos_data_helpers(self):
        model = self.env["multi.barcode.products"]

        self.assertEqual(model._load_pos_data_fields(False), [
            "multi_barcode",
            "product_id",
        ])
        self.assertEqual(model._load_pos_data_domain({}), [])

    def test_get_barcode_val(self):
        barcode = self.env["multi.barcode.products"].create({
            "multi_barcode": "ALT-001",
            "product_id": self.product.id,
        })

        self.assertEqual(barcode.get_barcode_val(self.product.id), (
            "ALT-001",
            self.product.id,
        ))
