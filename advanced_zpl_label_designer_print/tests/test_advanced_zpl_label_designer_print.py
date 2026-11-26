# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAdvancedZplLabelDesignerPrint(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_model = cls.env["ir.model"]._get("product.product")
        cls.name_field = cls.env["ir.model.fields"]._get("product.product", "name")
        cls.default_code_field = cls.env["ir.model.fields"]._get("product.product", "default_code")

        cls.product = cls.env["product.product"].create({
            "name": "ZPL Product",
            "list_price": 19.99,
            "default_code": "SKU-001",
            "barcode": "123456789012",
            "weight": 2.5,
            "description_sale": "Printable description",
        })
        cls.second_product = cls.env["product.product"].create({
            "name": "Second Product",
            "list_price": 29.99,
            "default_code": "SKU-002",
            "barcode": "999999999999",
        })

        cls.template = cls.env["zpl.label.template"].create({
            "name": "ZPL Template",
            "model_id": cls.product_model.id,
            "width": 101.6,
            "height": 152.4,
            "unit": "mm",
            "dpi": "203",
            "element_ids": [
                Command.create({
                    "name": "Product Name",
                    "type": "text",
                    "field_id": cls.name_field.id,
                    "data_format": "Product: {{value}}",
                    "x_pos": 10,
                    "y_pos": 20,
                    "font_size": 30,
                }),
                Command.create({
                    "name": "Price",
                    "type": "text",
                    "x_pos": 0,
                    "y_pos": 0,
                    "font_size": 22,
                }),
                Command.create({
                    "name": "Barcode",
                    "type": "barcode",
                    "field_id": cls.default_code_field.id,
                    "barcode_type": "code39",
                    "x_pos": 30,
                    "y_pos": 40,
                    "font_size": 90,
                }),
                Command.create({
                    "name": "QR Code",
                    "type": "qrcode",
                    "x_pos": 50,
                    "y_pos": 60,
                    "width": 80,
                }),
                Command.create({
                    "name": "Box",
                    "type": "rect",
                    "x_pos": 70,
                    "y_pos": 80,
                    "width": 100,
                    "height": 60,
                    "thickness": 3,
                    "rounding": 4,
                }),
                Command.create({
                    "name": "Divider",
                    "type": "line",
                    "x_pos": 5,
                    "y_pos": 6,
                    "width": 50,
                    "height": 0,
                    "thickness": 1,
                }),
                Command.create({
                    "name": "Logo",
                    "type": "image",
                    "x_pos": 1,
                    "y_pos": 2,
                }),
            ],
        })

    def test_generate_zpl_for_product_renders_expected_commands(self):
        zpl = self.template.generate_zpl_for_product(self.product)

        self.assertTrue(zpl.startswith("^XA"))
        self.assertTrue(zpl.endswith("^XZ"))
        self.assertIn("^FO16,40^A0N,30,30^FDProduct: ZPL Product^FS", zpl)
        self.assertIn("^FO0,0^A0N,22,22^FD19.99^FS", zpl)
        self.assertIn("^FO48,81^BY2^B3N,90,Y,N,N^FDSKU-001^FS", zpl)
        self.assertIn("^FO81,121^BQN,2,2^FDQA,QR Code^FS", zpl)
        self.assertIn("^FO113,162^GB162,121,3,B,4^FS", zpl)
        self.assertIn("^FO8,12^GB81,1,1,B,0^FS", zpl)
        self.assertIn("^FO1,4^FD[IMAGE: Logo]^FS", zpl)

    def test_save_design_from_js_replaces_elements_and_updates_zpl(self):
        template = self.env["zpl.label.template"].create({
            "name": "Saved Template",
            "model_id": self.product_model.id,
        })
        self.env["zpl.label.element"].create({
            "template_id": template.id,
            "name": "Old Element",
            "type": "text",
        })

        result = self.env["zpl.label.template"].save_design_from_js(template.id, [{
            "name": "New Barcode",
            "type": "barcode",
            "field_id": self.default_code_field.id,
            "barcode_type": "ean13",
            "x_pos": 25,
            "y_pos": 35,
            "width": 110,
            "height": 40,
            "font_size": 80,
        }])

        template.invalidate_recordset(["element_ids", "zpl_content"])
        self.assertTrue(result)
        self.assertEqual(template.element_ids.mapped("name"), ["New Barcode"])
        self.assertEqual(template.element_ids.barcode_type, "ean13")
        self.assertIn("^BEN,80,Y,N,N^FDNew Barcode^FS", template.zpl_content)

    def test_report_rendering_handles_records_preview_and_missing_template(self):
        report = self.env["ir.actions.report"]

        rendering, qweb_type = report._render_qweb_text(
            "advanced_zpl_label_designer_print.report_zpl_view",
            self.template.id,
            {
                "zpl_template_id": self.template.id,
                "product_ids": [self.product.id, self.second_product.id],
            },
        )

        text = rendering.decode("utf-8")
        self.assertEqual(qweb_type, "text")
        self.assertIn("Product: ZPL Product", text)
        self.assertIn("Product: Second Product", text)
        self.assertEqual(text.count("^XA"), 2)

        preview_rendering, preview_type = report._render_qweb_text(
            "advanced_zpl_label_designer_print.report_zpl_view",
            self.template.id,
            None,
        )
        self.assertEqual(preview_type, "text")
        self.assertEqual(preview_rendering.decode("utf-8"), self.template.zpl_content)

        error_rendering, error_type = report._render_qweb_text(
            "advanced_zpl_label_designer_print.report_zpl_view",
            [],
            {"zpl_template_id": 999999},
        )
        self.assertEqual(error_type, "text")
        self.assertEqual(error_rendering, b"^XA^FDTemplate Error^FS^XZ")

    def test_action_preview_returns_report_action(self):
        action = self.template.with_context(discard_logo_check=True).action_preview()

        self.assertEqual(action["type"], "ir.actions.report")
        self.assertEqual(action["report_name"], "advanced_zpl_label_designer_print.report_zpl_view")
        self.assertEqual(action["report_type"], "qweb-text")
        self.assertEqual(action["context"]["active_ids"], self.template.ids)

    def test_product_label_layout_requires_template_for_zpl(self):
        wizard = self.env["product.label.layout"].create({
            "print_format": "zpl_label_designer",
            "product_ids": [Command.set(self.product.ids)],
        })

        with self.assertRaises(UserError):
            wizard.process()

    def test_product_label_layout_process_builds_report_data(self):
        wizard = self.env["product.label.layout"].with_context(
            discard_logo_check=True
        ).create({
            "print_format": "zpl_label_designer",
            "zpl_template_id": self.template.id,
            "product_ids": [Command.set(self.product.ids)],
            "custom_quantity": 3,
        })

        action = wizard.process()

        self.assertEqual(action["type"], "ir.actions.report")
        self.assertEqual(action["report_name"], "advanced_zpl_label_designer_print.report_zpl_view")
        self.assertEqual(action["data"]["zpl_template_id"], self.template.id)
        self.assertEqual(action["data"]["product_ids"], self.product.ids)
        self.assertEqual(action["data"]["quantity"], 3)

    def test_product_label_layout_uses_template_variants_when_products_missing(self):
        wizard = self.env["product.label.layout"].with_context(
            discard_logo_check=True
        ).create({
            "print_format": "zpl_label_designer",
            "zpl_template_id": self.template.id,
            "product_tmpl_ids": [Command.set(self.product.product_tmpl_id.ids)],
        })

        action = wizard.process()

        self.assertEqual(action["data"]["product_ids"], self.product.product_tmpl_id.product_variant_ids.ids)
