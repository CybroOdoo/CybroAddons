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

class TestProductDelete(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Delete Product 1',
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Delete Product 2',
        })

    def test_delete_product(self):
        product_1_id = self.product_template_1.id
        product_2_id = self.product_template_2.id
        wizard = self.env['product.delete'].create({
            'product_ids': [product_1_id, product_2_id],
        })
        wizard.action_delete_product()
        
        deleted_products = self.env['product.template'].search([('id', 'in', [product_1_id, product_2_id])])
        self.assertFalse(deleted_products)
