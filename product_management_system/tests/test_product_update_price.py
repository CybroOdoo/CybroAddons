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

class TestProductUpdatePrice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Price Product 1',
            'list_price': 10.0,
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Price Product 2',
            'list_price': 20.0,
        })

    def test_product_update_price_confirm(self):
        wizard = self.env['product.update.price'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'product_price': 45.0,
        })
        wizard.action_product_update_price_confirm()
        self.assertEqual(self.product_template_1.list_price, 45.0)
        self.assertEqual(self.product_template_2.list_price, 45.0)

    def test_product_update_price_zero(self):
        wizard = self.env['product.update.price'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'product_price': 0.0,
        })
        wizard.action_product_update_price_confirm()
        self.assertEqual(self.product_template_1.list_price, 10.0)
        self.assertEqual(self.product_template_2.list_price, 20.0)
