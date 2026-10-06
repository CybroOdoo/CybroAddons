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
from odoo import Command

class TestProductRecommendation(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({'name': 'Vendor REC'})
        cls.po = cls.env['purchase.order'].create({'partner_id': cls.partner.id})
        cls.product = cls.env['product.product'].create({
            'name': 'Test REC Product',
            'type': 'consu',
        })

        cls.wizard = cls.env['product.recommendation'].with_context(active_id=cls.po.id).create({
            'line_ids': [Command.create({
                'product_id': cls.product.id,
                'qty_need': 5,
                'is_modified': True,
            })]
        })

    def test_default_order_id(self):
        """Test default active id fetching."""
        self.assertEqual(self.wizard.order_id.id, self.po.id)

    def test_add_to_order_line(self):
        """Test adding selected products to order line."""
        self.wizard.add_to_order_line()
        self.assertEqual(len(self.po.order_line), 1)
        self.assertEqual(self.po.order_line[0].product_qty, 5)
