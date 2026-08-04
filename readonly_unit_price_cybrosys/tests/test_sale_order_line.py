# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions
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
###############################################################################
from odoo.tests import TransactionCase

class TestSaleOrderLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSaleOrderLine, cls).setUpClass()
        
        cls.readonly_user = cls.env['res.users'].create({
            'name': 'Readonly Sales User',
            'login': 'readonly_sales_user',
            'email': 'readonly_sales@example.com',
            'readonly_unit_price_sales': True,
        })
        
        cls.normal_user = cls.env['res.users'].create({
            'name': 'Normal Sales User',
            'login': 'normal_sales_user',
            'email': 'normal_sales@example.com',
            'readonly_unit_price_sales': False,
        })

        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': True,
            'list_price': 100.0,
        })

    def test_compute_price_unit_boolean(self):
        """Test the _compute_price_unit_boolean method in sale.order.line"""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
            })]
        })
        line = sale_order.order_line[0]

        # Test as readonly user
        line.with_user(self.readonly_user)._compute_price_unit_boolean()
        self.assertTrue(line.with_user(self.readonly_user).price_unit_boolean, 
                        "Readonly user should have price_unit_boolean as True on sale line")

        # Test as normal user
        line.with_user(self.normal_user)._compute_price_unit_boolean()
        self.assertFalse(line.with_user(self.normal_user).price_unit_boolean, 
                         "Normal user should have price_unit_boolean as False on sale line")
