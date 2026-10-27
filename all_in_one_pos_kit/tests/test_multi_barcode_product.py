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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
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
            "product_multi_id",
            "template_multi_id",
        ])
        self.assertEqual(model._load_pos_data_domain({}, False), [])

    def test_get_barcode_val(self):
        barcode = self.env["multi.barcode.products"].create({
            "multi_barcode": "ALT-001",
            "product_multi_id": self.product.id,
            "template_multi_id": self.product.product_tmpl_id.id,
        })

        self.assertEqual(barcode.get_barcode_val("ALT-001"), (
            "ALT-001",
            self.product.product_tmpl_id.id,
        ))
