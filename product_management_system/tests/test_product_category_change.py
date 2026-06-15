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

class TestProductCategoryChange(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category_old = cls.env['product.category'].create({
            'name': 'Old Category',
        })
        cls.category_new = cls.env['product.category'].create({
            'name': 'New Category',
        })
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Cat Product 1',
            'categ_id': cls.category_old.id,
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Cat Product 2',
            'categ_id': cls.category_old.id,
        })

    def test_product_category_change_confirm(self):
        wizard = self.env['product.category.change'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'category_id': self.category_new.id,
        })
        wizard.action_product_category_change_confirm()
        self.assertEqual(self.product_template_1.categ_id, self.category_new)
        self.assertEqual(self.product_template_2.categ_id, self.category_new)
