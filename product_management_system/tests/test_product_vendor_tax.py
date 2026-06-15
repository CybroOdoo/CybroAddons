# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
from odoo.tests.common import TransactionCase

class TestProductVendorTax(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_purchase = cls.env['account.tax'].create({
            'name': 'Test Purchase Tax',
            'amount': 10.0,
            'type_tax_use': 'purchase',
        })
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Vendor Tax Product 1',
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Vendor Tax Product 2',
        })

    def test_change_vendor_tax(self):
        wizard = self.env['product.vendor.tax'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'tax_ids': [self.tax_purchase.id],
        })
        wizard.action_change_vendor_tax()
        self.assertIn(self.tax_purchase, self.product_template_1.supplier_taxes_id)
        self.assertIn(self.tax_purchase, self.product_template_2.supplier_taxes_id)
