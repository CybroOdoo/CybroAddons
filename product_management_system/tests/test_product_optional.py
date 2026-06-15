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

class TestProductOptional(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Main Product 1',
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Main Product 2',
        })
        cls.opt_product = cls.env['product.template'].create({
            'name': 'Optional Product',
        })

    def test_add_optional_products(self):
        wizard = self.env['product.optional'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'optional_ids': [self.opt_product.id],
        })
        wizard.action_add_optional_products()
        self.assertIn(self.opt_product, self.product_template_1.optional_product_ids)
        self.assertIn(self.opt_product, self.product_template_2.optional_product_ids)
