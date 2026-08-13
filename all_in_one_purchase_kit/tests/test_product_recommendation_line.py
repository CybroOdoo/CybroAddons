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
class TestProductRecommendationLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Recommendation Line Vendor'})
        cls.product = cls.env['product.product'].create({
            'name': 'Recommended Product Line',
            'type': 'consu',
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })
        cls.wizard = cls.env['product.recommendation'].create({
            'order_id': cls.po.id,
        })

    def test_product_recommendation_line(self):
        """Test product recommendation line methods and field updates."""
        line = self.env['product.recommendation.line'].create({
            'recommendation_id': self.wizard.id,
            'product_id': self.product.id,
            'qty_need': 12,
            'is_modified': True,
        })
        
        # Test related values
        self.assertEqual(line.currency_id, self.product.currency_id)
        self.assertEqual(line.partner_id, self.partner)
        
        # Test _prepare_order_line
        vals = line._prepare_order_line(sequence=2)
        self.assertEqual(vals['order_id'], self.po.id)
        self.assertEqual(vals['product_id'], self.product.id)
        self.assertEqual(vals['sequence'], 2)
        self.assertEqual(vals['product_qty'], 12)
