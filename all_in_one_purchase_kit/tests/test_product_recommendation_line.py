# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

###############################################################################
from odoo.tests.common import TransactionCase

class TestProductRecommendationLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({'name': 'Vendor RECL'})
        cls.po = cls.env['purchase.order'].create({'partner_id': cls.partner.id})
        cls.product = cls.env['product.product'].create({
            'name': 'Test RECL Product',
            'type': 'consu',
        })

        cls.wizard = cls.env['product.recommendation'].with_context(active_id=cls.po.id).create({})
        cls.line = cls.env['product.recommendation.line'].create({
            'recommendation_id': cls.wizard.id,
            'product_id': cls.product.id,
            'qty_need': 10,
        })

    def test_prepare_order_line(self):
        """Test prepare order line dict."""
        vals = self.line._prepare_order_line(1)
        self.assertEqual(vals['order_id'], self.po.id)
        self.assertEqual(vals['product_id'], self.product.id)
        self.assertEqual(vals['sequence'], 1)
        self.assertEqual(vals['product_qty'], 10)
