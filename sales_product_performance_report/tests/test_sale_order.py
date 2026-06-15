# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase

class TestSaleOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.env.ref('base.partner_admin').id,
        })

    def test_actions(self):
        # Test action_product_performance_report
        res_prod = self.sale_order.action_product_performance_report()
        self.assertEqual(res_prod.get('res_model'), 'product.performance')
        self.assertEqual(res_prod.get('target'), 'new')
        self.assertEqual(res_prod.get('view_mode'), 'form')

        # Test action_sales_performance_report
        res_sales = self.sale_order.action_sales_performance_report()
        self.assertEqual(res_sales.get('res_model'), 'sales.performance')
        self.assertEqual(res_sales.get('target'), 'new')
        self.assertEqual(res_sales.get('view_mode'), 'form')
