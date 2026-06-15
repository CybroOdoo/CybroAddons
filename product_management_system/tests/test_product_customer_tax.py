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

class TestProductCustomerTax(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_sale = cls.env['account.tax'].create({
            'name': 'Test Sale Tax',
            'amount': 15.0,
            'type_tax_use': 'sale',
        })
        cls.product_template_1 = cls.env['product.template'].create({
            'name': 'Tax Product 1',
        })
        cls.product_template_2 = cls.env['product.template'].create({
            'name': 'Tax Product 2',
        })

    def test_change_customer_tax(self):
        wizard = self.env['product.customer.tax'].create({
            'product_ids': [self.product_template_1.id, self.product_template_2.id],
            'tax_ids': [self.tax_sale.id],
        })
        wizard.action_change_customer_tax()
        self.assertIn(self.tax_sale, self.product_template_1.taxes_id)
        self.assertIn(self.tax_sale, self.product_template_2.taxes_id)
