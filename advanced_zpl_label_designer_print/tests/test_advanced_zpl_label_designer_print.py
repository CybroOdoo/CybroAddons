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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAdvancedZplLabelDesignerPrint(TransactionCase):
    """Tests for ZPL template generation, JS design saving, and the
    custom report/print-wizard integration."""

    @classmethod
    def setUpClass(cls):
        """Create shared model references and two test products used
        across the individual test methods."""
        super().setUpClass()
        cls.report_model = cls.env["ir.actions.report"]
        cls.template_model = cls.env["zpl.label.template"]
        cls.element_model = cls.env["zpl.label.element"]
        cls.layout_model = cls.env["product.label.layout"]
        cls.product_model_ref = cls.env["ir.model"]._get("product.product")
        cls.default_code_field = cls.env["ir.model.fields"].search([
            ("model", "=", "product.product"),
            ("name", "=", "default_code"),
        ], limit=1)
        cls.barcode_field = cls.env["ir.model.fields"].search([
            ("model", "=", "product.product"),
            ("name", "=", "barcode"),
        ], limit=1)

        cls.product_one = cls.env["product.template"].create({
            "name": "ZPL Product One",
            "barcode": "123456789012",
            "default_code": "SKU-001",
            "list_price": 12.5,
            "weight": 1.25,
        }).product_variant_id
        cls.product_two = cls.env["product.template"].create({
            "name": "ZPL Product Two",
            "barcode": "987654321098",
            "default_code": "SKU-002",
            "list_price": 18.0,
            "weight": 2.50,
        }).product_variant_id

    def _create_template(self, name="Template"):
        """Create a ``zpl.label.template`` bound to ``product.product``
        with a small 2x1 inch size, for use as a test fixture."""
        return self.template_model.create({
            "name": name,
            "model_id": self.product_model_ref.id,
            "width": 50.8,
            "height": 25.4,
            "unit": "mm",
            "dpi": "203",
        })

    def test_generate_zpl_for_product_uses_field_mapping_and_element_types(self):
        """Every element type (text, barcode, qrcode, rect, line) should
        render its expected ZPL command, with text/barcode/qrcode content
        pulled from the mapped field and formatted via data_format."""
        template = self._create_template("Mapped Template")
        self.element_model.create([
            {
                "template_id": template.id,
                "name": "Product Name",
                "type": "text",
                "x_pos": 10,
                "y_pos": 20,
                "font_size": 30,
                "field_id": self.default_code_field.id,
                "data_format": "SKU: {{value}}",
            },
            {
                "template_id": template.id,
                "name": "Product Barcode",
                "type": "barcode",
                "x_pos": 40,
                "y_pos": 80,
                "font_size": 90,
                "barcode_type": "code39",
                "field_id": self.barcode_field.id,
            },
            {
                "template_id": template.id,
                "name": "QR Payload",
                "type": "qrcode",
                "x_pos": 60,
                "y_pos": 140,
                "width": 120,
                "field_id": self.barcode_field.id,
            },
            {
                "template_id": template.id,
                "name": "Box",
                "type": "rect",
                "x_pos": 5,
                "y_pos": 5,
                "width": 200,
                "height": 80,
                "thickness": 3,
                "rounding": 2,
            },
            {
                "template_id": template.id,
                "name": "Divider",
                "type": "line",
                "x_pos": 5,
                "y_pos": 100,
                "width": 180,
                "height": 2,
                "thickness": 4,
            },
        ])

        zpl = template.generate_zpl_for_product(self.product_one)

        self.assertTrue(zpl.startswith("^XA"))
        self.assertTrue(zpl.endswith("^XZ"))
        self.assertIn("SKU: SKU-001", zpl)
        self.assertIn("^B3N,90,Y,N,N^FD123456789012^FS", zpl)
        self.assertIn("^BQN,2,", zpl)
        self.assertIn("^FDQA,123456789012^FS", zpl)
        self.assertIn("^GB", zpl)

    def test_save_design_from_js_replaces_elements_and_updates_zpl_content(self):
        """save_design_from_js should drop existing elements, create the
        new ones from the JS payload, and refresh the sample ZPL code."""
        template = self._create_template("JS Save Template")
        self.element_model.create({
            "template_id": template.id,
            "name": "Old Element",
            "type": "text",
        })

        result = template.save_design_from_js(template.id, [
            {
                "name": "Saved Text",
                "type": "text",
                "x_pos": 15,
                "y_pos": 25,
                "font_size": 24,
                "field_id": self.default_code_field.id,
            },
            {
                "name": "Saved Rectangle",
                "type": "rect",
                "x_pos": 30,
                "y_pos": 40,
                "width": 150,
                "height": 60,
                "thickness": 2,
                "rounding": 1,
            },
        ])

        self.assertTrue(result)
        self.assertCountEqual(
            template.element_ids.mapped("name"),
            ["Saved Text", "Saved Rectangle"],
        )
        self.assertNotIn("Old Element", template.element_ids.mapped("name"))
        self.assertIn("Saved Text", template.zpl_content)
        self.assertIn("^GB", template.zpl_content)

    def test_render_qweb_text_returns_template_error_for_missing_template(self):
        """Rendering with an id that matches no template should return
        the fallback error ZPL instead of raising."""
        content, extension = self.report_model._render_qweb_text(
            "advanced_zpl_label_designer_print.report_zpl_view",
            [999999],
            data={},
        )

        self.assertEqual(content, b"^XA^FDTemplate Error^FS^XZ")
        self.assertEqual(extension, "txt")

    def test_render_qweb_text_generates_zpl_for_each_product(self):
        """When product_ids are passed in the report data, one ZPL label
        block should be generated per product."""
        template = self._create_template("Render Template")
        self.element_model.create({
            "template_id": template.id,
            "name": "Product Name",
            "type": "text",
        })

        content, extension = self.report_model._render_qweb_text(
            "advanced_zpl_label_designer_print.report_zpl_view",
            [template.id],
            data={
                "zpl_template_id": template.id,
                "product_ids": [self.product_one.id, self.product_two.id],
            },
        )
        zpl = content.decode("utf-8")

        self.assertEqual(extension, "txt")
        self.assertEqual(zpl.count("^XA"), 2)
        self.assertIn("ZPL Product One", zpl)
        self.assertIn("ZPL Product Two", zpl)

    def test_render_qweb_text_returns_preview_when_no_products_are_given(self):
        """With no product ids in the report data, the static sample ZPL
        code on the template should be returned as-is."""
        template = self._create_template("Preview Template")
        self.element_model.create({
            "template_id": template.id,
            "name": "Preview Name",
            "type": "text",
        })

        content, extension = self.report_model._render_qweb_text(
            "advanced_zpl_label_designer_print.report_zpl_view",
            [template.id],
            data={"zpl_template_id": template.id},
        )

        self.assertEqual(content.decode("utf-8"), template.zpl_content)
        self.assertEqual(extension, "txt")

    def test_product_label_layout_requires_template_for_zpl_format(self):
        """The print wizard should refuse to process the ZPL label
        format if no ZPL template was selected."""
        wizard = self.layout_model.create({
            "print_format": "advanced_zpl_label_designer_print",
            "custom_quantity": 1,
            "product_ids": [(6, 0, [self.product_one.id])],
        })

        with self.assertRaisesRegex(
            UserError,
            "Please select a ZPL Template before printing.",
        ):
            wizard.process()
