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

class TestProductAccessory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Base Product 1',
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Base Product 2',
        })
        cls.accessory_product = cls.env['product.product'].create({
            'name': 'Accessory Product',
        })

    def test_add_accessory_products(self):
        wizard = self.env['product.accessory'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'accessory_ids': [self.accessory_product.id],
        })
        wizard.action_add_accessory_products()
        self.assertIn(self.accessory_product, self.product_template_1.accessory_product_ids)
        self.assertIn(self.accessory_product, self.product_template_2.accessory_product_ids)
