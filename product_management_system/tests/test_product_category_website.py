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

class TestProductCategoryWebsite(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.public_category = cls.env['product.public.category'].create({
            'name': 'Website Category',
        })
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Web Cat Product 1',
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Web Cat Product 2',
        })

    def test_change_website_category(self):
        wizard = self.env['product.category.website'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'public_categ_ids': [self.public_category.id],
        })
        wizard.action_change_website_category()
        self.assertIn(self.public_category, self.product_template_1.public_categ_ids)
        self.assertIn(self.public_category, self.product_template_2.public_categ_ids)
