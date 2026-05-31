# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDuplicateProductBom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.finished_template = cls.env["product.template"].create({
            "name": "Finished Product",
            "type": "consu",
            "uom_id": cls.uom_unit.id,
            "uom_po_id": cls.uom_unit.id,
        })
        cls.component_a = cls.env["product.product"].create({
            "name": "Component A",
            "type": "consu",
            "uom_id": cls.uom_unit.id,
            "uom_po_id": cls.uom_unit.id,
        })
        cls.component_b = cls.env["product.product"].create({
            "name": "Component B",
            "type": "consu",
            "uom_id": cls.uom_unit.id,
            "uom_po_id": cls.uom_unit.id,
        })
        cls.source_bom = cls.env["mrp.bom"].create({
            "product_tmpl_id": cls.finished_template.id,
            "product_qty": 2.0,
            "code": "BOM-FINISHED",
            "bom_line_ids": [
                (0, 0, {
                    "product_id": cls.component_a.id,
                    "product_qty": 3.0,
                }),
                (0, 0, {
                    "product_id": cls.component_b.id,
                    "product_qty": 5.0,
                }),
            ],
        })

    def test_copy_duplicates_bom_and_bom_lines(self):
        duplicated_template = self.finished_template.copy({
            "name": "Finished Product Copy",
        })

        self.assertNotEqual(duplicated_template.id, self.finished_template.id)
        duplicated_bom = self.env["mrp.bom"].search([
            ("product_tmpl_id", "=", duplicated_template.id),
        ])
        self.assertEqual(len(duplicated_bom), 1)
        self.assertNotEqual(duplicated_bom.id, self.source_bom.id)
        self.assertEqual(duplicated_bom.product_qty, self.source_bom.product_qty)
        self.assertEqual(duplicated_bom.code, self.source_bom.code)
        self.assertEqual(duplicated_bom.type, self.source_bom.type)

        copied_lines = duplicated_bom.bom_line_ids.sorted("product_id")
        source_lines = self.source_bom.bom_line_ids.sorted("product_id")
        self.assertEqual(len(copied_lines), len(source_lines))
        self.assertEqual(
            copied_lines.mapped("product_id"),
            source_lines.mapped("product_id"),
        )
        self.assertEqual(
            copied_lines.mapped("product_qty"),
            source_lines.mapped("product_qty"),
        )
