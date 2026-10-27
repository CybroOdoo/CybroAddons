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
class TestProductProduct(TransactionCase):

    def test_load_pos_data_fields_include_custom_fields(self):
        config = self.env["pos.config"].search([], limit=1) or \
            self.env["pos.config"].create({"name": "Product Test POS"})
        fields = self.env["product.product"]._load_pos_data_fields(config)

        self.assertIn("is_age_restrict", fields)

    def test_create_updates_multi_barcode_template(self):
        product = self.env["product.product"].create({
            "name": "Variant Barcode Product",
            "product_multi_barcodes_ids": [(0, 0, {
                "multi_barcode": "VAR-001",
            })],
        })

        self.assertEqual(
            product.product_multi_barcodes_ids.template_multi_id,
            product.product_tmpl_id,
        )

    def test_onchange_to_make_mrp_requires_bom(self):
        product = self.env["product.product"].create({
            "name": "MRP Product Without BOM",
        })
        product.to_make_mrp = True

        with self.assertRaises(ValidationError):
            product.onchange_to_make_mrp()
