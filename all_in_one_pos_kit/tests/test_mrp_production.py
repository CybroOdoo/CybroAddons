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
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMrpProductionFromPos(TransactionCase):

    def test_create_mrp_from_pos_without_products_raises(self):
        with self.assertRaises(UserError):
            self.env["mrp.production"].create_mrp_from_pos([])

    def test_create_mrp_from_pos_without_valid_products_raises(self):
        with self.assertRaises(UserError):
            self.env["mrp.production"].create_mrp_from_pos([
                {"id": False, "qty": 1},
                {"id": 1, "qty": 0},
            ])

    def test_create_mrp_from_pos_skips_products_without_bom(self):
        product = self.env["product.product"].create({"name": "No BoM"})
        result = self.env["mrp.production"].create_mrp_from_pos([
            {"id": product.id, "qty": 2, "pos_reference": "POS-1"},
        ])
        self.assertTrue(result)
        self.assertFalse(self.env["mrp.production"].search(
            [("product_id", "=", product.id)]))

    def _make_product_with_bom(self, name, to_make_mrp):
        component = self.env["product.product"].create(
            {"name": "%s component" % name})
        product = self.env["product.product"].create(
            {"name": name, "to_make_mrp": to_make_mrp})
        self.env["mrp.bom"].create({
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_qty": 1,
            "bom_line_ids": [(0, 0, {
                "product_id": component.id, "product_qty": 1})],
        })
        return product

    def test_create_mrp_from_pos_only_for_flagged_products(self):
        flagged = self._make_product_with_bom("Flagged", True)
        not_flagged = self._make_product_with_bom("Not flagged", False)
        self.env["mrp.production"].create_mrp_from_pos([
            {"id": flagged.id, "qty": 1, "pos_reference": "POS-2"},
            {"id": not_flagged.id, "qty": 1, "pos_reference": "POS-2"},
        ])
        mrp = self.env["mrp.production"]
        self.assertTrue(mrp.search([("product_id", "=", flagged.id)]))
        self.assertFalse(mrp.search([("product_id", "=", not_flagged.id)]))
