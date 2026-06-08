# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
from datetime import datetime, timedelta

class TestStockMove(TransactionCase):
    def setUp(self):
        super(TestStockMove, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test CW Product',
            'type': 'consu', 'is_storable': True,
            'barcode': 'cw123',
            'catch_weight_ok': True,
            'average_cw_qty': 2.0,
        })
        self.picking_type_out = self.env['stock.picking.type'].search([('code', '=', 'outgoing')], limit=1)
        self.location_src = self.picking_type_out.default_location_src_id
        self.location_dest = self.picking_type_out.default_location_dest_id
        
        self.picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        
        self.move = self.env['stock.move'].create({
            'product_id': self.product.id,
            'product_uom': self.product.uom_id.id,
            'product_uom_qty': 5.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
            'picking_id': self.picking.id,
        })

    def test_barcode_assignment(self):
        # Test create and write auto-fills barcode
        self.assertEqual(self.move.barcode, 'cw123')
        
        product_no_barcode = self.env['product.product'].create({
            'name': 'No Barcode',
            'type': 'consu', 'is_storable': True
        })
        move_no_barcode = self.env['stock.move'].create({
            'product_id': product_no_barcode.id,
            'product_uom': product_no_barcode.uom_id.id,
            'product_uom_qty': 1.0,
            'location_id': self.location_src.id,
            'location_dest_id': self.location_dest.id,
        })
        self.assertFalse(move_no_barcode.barcode)

    def test_cw_computations(self):
        # cw_qty_done
        self.move.product_uom_qty = 5.0
        self.move._compute_cw_qty_done()
        self.assertEqual(self.move.cw_qty_done, 10.0) # 5 * 2.0
        
        # cw_hide
        self.move._compute_cw_hide()
        self.assertTrue(self.move.cw_hide)
        
        # _cal_cw_demand
        self.move._cal_cw_demand()
        self.assertEqual(self.move.cw_demand, 10.0)
        self.assertEqual(self.move.cw_reserved, 10.0)

    def test_onchanges(self):
        # _onchange_product_id
        self.move._onchange_product_id()
        self.assertEqual(self.move.cw_demand, 10.0)
        
        # _onchange_cw_done
        self.move.cw_done = 4.0
        self.move._onchange_cw_done()
        self.assertEqual(self.move.quantity, 2.0)
        
        # onchange_cw_demand
        self.move.cw_demand = 8.0
        self.move.onchange_cw_demand()
        self.assertEqual(self.move.product_uom_qty, 4.0)

    def test_dashboard_data(self):
        # Test the rpc methods that fetch dashboard data
        # _cr.execute fetches depend on existing data, so we mainly check they run without error and return correct structure
        top_10 = self.env['stock.move'].top_products_last_ten()
        self.assertIn('products', top_10)
        
        top_30 = self.env['stock.move'].top_products_last_thirty()
        self.assertIn('products', top_30)
        
        top_3_months = self.env['stock.move'].top_products_last_three_months()
        self.assertIn('products', top_3_months)
        
        top_year = self.env['stock.move'].top_products_last_year()
        self.assertIn('products', top_year)
        
        stock_moves = self.env['stock.move'].get_stock_moves()
        self.assertIn('name', stock_moves)
        
        last_ten_days = self.env['stock.move'].stock_move_last_ten_days({})
        self.assertIn('name', last_ten_days)
        
        this_month = self.env['stock.move'].this_month({})
        self.assertIn('name', this_month)
        
        last_three_month = self.env['stock.move'].last_three_month({})
        self.assertIn('name', last_three_month)
        
        last_year_moves = self.env['stock.move'].last_year({})
        self.assertIn('name', last_year_moves)
        
        dead_stock = self.env['stock.move'].get_dead_of_stock()
        if dead_stock:
            self.assertIn('product_name', dead_stock)
