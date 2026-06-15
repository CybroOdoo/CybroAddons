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

class TestProductMakePurchasable(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Purchasable Product 1',
            'purchase_ok': False,
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Purchasable Product 2',
            'purchase_ok': True,
        })

    def test_product_make_purchasable_confirm(self):
        wizard = self.env['product.make.purchasable'].create({
            'product_ids': [self.product_template_1.id],
        })
        wizard.action_product_make_purchasable_confirm()
        self.assertTrue(self.product_template_1.purchase_ok)

    def test_product_make_purchasable_false(self):
        wizard = self.env['product.make.purchasable'].create({
            'product_ids': [self.product_template_2.id],
        })
        wizard.action_product_make_purchasable_false()
        self.assertFalse(self.product_template_2.purchase_ok)
