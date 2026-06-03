# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestProductProduct(TransactionCase):

    def test_load_pos_data_fields_include_custom_fields(self):
        fields = self.env["product.product"]._load_pos_data_fields(False)

        self.assertIn("is_age_restrict", fields)
        self.assertIn("to_make_mrp", fields)

    def test_create_updates_multi_barcode_template(self):
        product = self.env["product.product"].create({
            "name": "Variant Barcode Product",
            "product_multi_barcodes_ids": [(0, 0, {
                "multi_barcode": "VAR-001",
            })],
        })

        self.assertEqual(
            product.product_multi_barcodes_ids.product_template_id,
            product.product_tmpl_id,
        )

    def test_onchange_to_make_mrp_requires_bom(self):
        product = self.env["product.product"].create({
            "name": "MRP Product Without BOM",
        })
        product.to_make_mrp = True

        with self.assertRaises(Warning):
            product._onchange_to_make_mrp()
