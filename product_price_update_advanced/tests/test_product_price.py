# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil (odoo@cybrosys.com)
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


class TestProductPrice(TransactionCase):

    def setUp(self):
        super().setUp()

        self.product_template = self.env.ref(
            'product.product_product_4'
        ).product_tmpl_id

    def test_action_change_product_price(self):
        """Test updating sale and cost price using wizard"""

        wizard = self.env['product.price'].create({
            'product_id': self.product_template.id,
            'sale_price': 200,
            'cost_price': 120,
        })

        result = wizard.action_change_product_price()

        self.assertEqual(self.product_template.list_price, 200)
        self.assertEqual(self.product_template.standard_price, 120)

        self.assertEqual(result['res_model'], 'product.template')
        self.assertEqual(result['res_id'], self.product_template.id)

    def test_onchange_product_id(self):
        """Test onchange method updates wizard fields"""

        wizard = self.env['product.price'].new({
            'product_id': self.product_template.id,
        })

        wizard._onchange_name()

        self.assertEqual(
            wizard.sale_price,
            self.product_template.list_price
        )

        self.assertEqual(
            wizard.cost_price,
            self.product_template.standard_price
        )
