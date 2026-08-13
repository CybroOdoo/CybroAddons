# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestProductRecommendation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Recommendation Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Recommended Product',
            'type': 'consu',
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_product_recommendation_wizard(self):
        """Test product recommendation wizard default order and adding to order line."""
        # Test default order_id from context active_id
        wizard_class = self.env['product.recommendation'].with_context(active_id=self.po.id)
        default_order = wizard_class._default_order_id()
        self.assertEqual(default_order, self.po.id)
        
        wizard = wizard_class.create({
            'order_id': self.po.id,
            'line_ids': [(0, 0, {
                'product_id': self.product.id,
                'list_price': 10.0,
                'available_qty': 100,
                'qty_need': 5,
                'is_modified': True,
            })]
        })
        
        self.assertEqual(len(self.po.order_line), 0)
        # Trigger adding to order line
        wizard.add_to_order_line()
        self.assertEqual(len(self.po.order_line), 1)
        self.assertEqual(self.po.order_line.product_id, self.product)
        self.assertEqual(self.po.order_line.product_qty, 5)
