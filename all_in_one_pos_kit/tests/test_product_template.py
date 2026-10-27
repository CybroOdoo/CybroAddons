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
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):

    def test_create_updates_multi_barcode_product(self):
        template = self.env["product.template"].create({
            "name": "Template Barcode Product",
            "template_multi_barcodes_ids": [(0, 0, {
                "multi_barcode": "TMPL-001",
            })],
        })

        self.assertEqual(
            template.template_multi_barcodes_ids.product_multi_id,
            template.product_variant_id,
        )

    def test_write_updates_multi_barcode_product(self):
        template = self.env["product.template"].create({
            "name": "Template Barcode Write Product",
            "template_multi_barcodes_ids": [(0, 0, {
                "multi_barcode": "TMPL-002",
            })],
        })

        template.write({"name": "Template Barcode Write Product Updated"})

        self.assertEqual(
            template.template_multi_barcodes_ids.product_multi_id,
            template.product_variant_id,
        )

    def test_onchange_to_make_mrp_requires_bom(self):
        template = self.env["product.template"].create({
            "name": "Template Without BOM",
        })
        template.to_make_mrp = True

        with self.assertRaises(ValidationError):
            template.onchange_to_make_mrp()
