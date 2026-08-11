# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Manasa T P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase


class TestInventoryDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create categories
        cls.category_1 = cls.env['product.category'].create({'name': 'Category 1'})
        cls.category_2 = cls.env['product.category'].create({'name': 'Category 2'})

        # Create products
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Product 1',
            'type': 'consu',
            'categ_id': cls.category_1.id,
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Product 2',
            'type': 'consu',
            'categ_id': cls.category_2.id,
        })

        cls.location_stock = cls.env.ref('stock.stock_location_stock')
        cls.location_customers = cls.env.ref('stock.stock_location_customers')
        cls.picking_type_out = cls.env.ref('stock.picking_type_out')

        # Add initial stock
        cls.env['stock.quant'].create({
            'product_id': cls.product_1.id,
            'location_id': cls.location_stock.id,
            'quantity': 100,
        })

        cls.env['stock.quant'].create({
            'product_id': cls.product_2.id,
            'location_id': cls.location_stock.id,
            'quantity': -5,
        })

        # Create picking
        cls.picking_1 = cls.env['stock.picking'].create({
            'location_id': cls.location_stock.id,
            'location_dest_id': cls.location_customers.id,
            'picking_type_id': cls.picking_type_out.id,
        })

        cls.move_1 = cls.env['stock.move'].create({
            'name': 'Move 1',
            'product_id': cls.product_1.id,
            'product_uom_qty': 10,
            'product_uom': cls.product_1.uom_id.id,
            'location_id': cls.location_stock.id,
            'location_dest_id': cls.location_customers.id,
            'picking_id': cls.picking_1.id,
        })

        cls.picking_1.action_confirm()
        cls.picking_1.action_assign()

        # Set settings
        cls.env['ir.config_parameter'].sudo().set_param("inventory_stock_dashboard_odoo.out_of_stock", "True")
        cls.env['ir.config_parameter'].sudo().set_param("inventory_stock_dashboard_odoo.out_of_stock_quantity", "5")

        cls.env['ir.config_parameter'].sudo().set_param("inventory_stock_dashboard_odoo.dead_stock_bol", "True")
        cls.env['ir.config_parameter'].sudo().set_param("inventory_stock_dashboard_odoo.dead_stock", "50")
        cls.env['ir.config_parameter'].sudo().set_param("inventory_stock_dashboard_odoo.dead_stock_type", "day")

    def test_stock_move_dashboard_methods(self):
        """ Test stock.move methods for dashboard."""

        # We process the picking to make state 'done'
        # To avoid actual inventory process we can force the state and flush for the query
        self.move_1.write({'state': 'done'})
        self.env.cr.execute("UPDATE stock_move SET state='done' WHERE id=%s", (self.move_1.id,))
        self.env.cr.execute("UPDATE stock_move_line SET state='done' WHERE move_id=%s", (self.move_1.id,))

        top_products = self.env['stock.move'].get_the_top_products()
        self.assertTrue(isinstance(top_products, dict))
        self.assertIn('products', top_products)
        self.assertIn('count', top_products)

        top_products_10 = self.env['stock.move'].top_products_last_ten()
        self.assertTrue(isinstance(top_products_10, dict))

        top_products_30 = self.env['stock.move'].top_products_last_thirty()
        self.assertTrue(isinstance(top_products_30, dict))

        top_products_3m = self.env['stock.move'].top_products_last_three_months()
        self.assertTrue(isinstance(top_products_3m, dict))

        top_products_1y = self.env['stock.move'].top_products_last_year()
        self.assertTrue(isinstance(top_products_1y, dict))

        stock_moves = self.env['stock.move'].get_stock_moves()
        self.assertTrue(isinstance(stock_moves, dict))
        self.assertIn('name', stock_moves)
        self.assertIn('count', stock_moves)

        stock_moves_10 = self.env['stock.move'].stock_move_last_ten_days({})
        self.assertTrue(isinstance(stock_moves_10, dict))

        stock_moves_this_month = self.env['stock.move'].this_month({})
        self.assertTrue(isinstance(stock_moves_this_month, dict))

        stock_moves_last_3_months = self.env['stock.move'].last_three_month({})
        self.assertTrue(isinstance(stock_moves_last_3_months, dict))

        stock_moves_last_year = self.env['stock.move'].last_year({})
        self.assertTrue(isinstance(stock_moves_last_year, dict))

        dead_stock = self.env['stock.move'].get_dead_of_stock()
        self.assertTrue(isinstance(dead_stock, dict))
        self.assertIn('product_name', dead_stock)
        self.assertIn('total_quantity', dead_stock)

    def test_stock_picking_dashboard_methods(self):
        """ Test stock.picking methods for dashboard."""

        res = self.env['stock.picking'].get_operation_types()
        self.assertEqual(len(res), 5)
        no_transfer, late, waiting, operation_type_name, backorder = res

        self.assertTrue(isinstance(no_transfer, dict))
        self.assertTrue(isinstance(late, dict))
        self.assertTrue(isinstance(waiting, dict))
        self.assertTrue(isinstance(operation_type_name, dict))
        self.assertTrue(isinstance(backorder, dict))

        product_categories = self.env['stock.picking'].get_product_category()
        self.assertTrue(isinstance(product_categories, dict))
        self.assertIn('name', product_categories)
        self.assertIn('count', product_categories)
        self.assertIn('Category 1', product_categories['name'])

        locations = self.env['stock.picking'].get_locations()
        self.assertTrue(isinstance(locations, dict))

    def test_stock_quant_dashboard_methods(self):
        """ Test stock.quant methods for dashboard."""
        out_of_stock = self.env['stock.quant'].get_out_of_stock()
        self.assertTrue(isinstance(out_of_stock, dict))
        self.assertIn('product_name', out_of_stock)
        self.assertIn('total_quantity', out_of_stock)

    def test_stock_move_line_dashboard_methods(self):
        """ Test stock.move.line methods for dashboard."""
        product_moves, category = self.env['stock.move.line'].get_product_moves()
        self.assertTrue(isinstance(product_moves, dict))
        self.assertTrue(isinstance(category, dict))
        self.assertIn('name', product_moves)
        self.assertIn('count', product_moves)
        self.assertIn('category_id', category)
        self.assertIn('category_name', category)

        # Assuming we got at least one category in the setup
        if category.get('category_id'):
            cat_id = category['category_id'][0]
            move_by_cat = self.env['stock.move.line'].product_move_by_category(cat_id)
            self.assertTrue(isinstance(move_by_cat, dict))
            self.assertIn('name', move_by_cat)
            self.assertIn('count', move_by_cat)

        # Test None option
        empty_res = self.env['stock.move.line'].product_move_by_category(None)
        self.assertEqual(empty_res, {})
