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


class TestStockPicking(TransactionCase):
    def setUp(self):
        super(TestStockPicking, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        if self.picking_type:
            self.picking = self.env['stock.picking'].create({
                'partner_id': self.partner.id,
                'picking_type_id': self.picking_type.id,
                'location_id': self.env.ref('stock.stock_location_stock').id,
                'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            })
    
    def test_stock_picking_creation(self):
        """Test stock picking creation with partner"""
        if self.picking_type:
            self.assertEqual(self.picking.partner_id, self.partner)
            
    def test_get_product_category(self):
        """Test get_product_category rpc method"""
        res = self.env['stock.picking'].get_product_category()
        self.assertTrue(isinstance(res, dict))
        self.assertIn('name', res)
        self.assertIn('count', res)
