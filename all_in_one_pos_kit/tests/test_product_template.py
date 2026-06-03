# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestProductTemplate(TransactionCase):

    def test_create_updates_multi_barcode_product(self):
        template = self.env["product.template"].create({
            "name": "Template Barcode Product",
            "product_template_ids": [(0, 0, {
                "multi_barcode": "TMPL-001",
            })],
        })

        self.assertEqual(
            template.product_template_ids.product_id,
            template.product_variant_id,
        )

    def test_write_updates_multi_barcode_product(self):
        template = self.env["product.template"].create({
            "name": "Template Barcode Write Product",
            "product_template_ids": [(0, 0, {
                "multi_barcode": "TMPL-002",
            })],
        })

        template.write({"name": "Template Barcode Write Product Updated"})

        self.assertEqual(
            template.product_template_ids.product_id,
            template.product_variant_id,
        )

    def test_onchange_to_make_mrp_requires_bom(self):
        template = self.env["product.template"].create({
            "name": "Template Without BOM",
        })
        template.to_make_mrp = True

        with self.assertRaises(ValidationError):
            template._onchange_to_make_mrp()
