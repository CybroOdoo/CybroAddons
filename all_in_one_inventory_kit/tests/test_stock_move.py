# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestStockMove(TransactionCase):
    def setUp(self):
        super(TestStockMove, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'product',
        })
        self.location = self.env.ref('stock.stock_location_stock')
        self.location_dest = self.env.ref('stock.stock_location_customers')
        self.move = self.env['stock.move'].create({
            'name': 'Test Move',
            'product_id': self.product.id,
            'location_id': self.location.id,
            'location_dest_id': self.location_dest.id,
            'product_uom': self.product.uom_id.id,
        })
    def test_stock_move(self):
        """Test stock move logic presence"""
        self.assertEqual(self.move.product_id, self.product)
