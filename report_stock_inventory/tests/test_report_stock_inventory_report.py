# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
#############################################################################
from datetime import timedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestReportStockInventoryReport(TransactionCase):
    """Test cases for report/report_stock_inventory_report.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['report.report_stock_inventory.report_stock_pdf']
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1
        )
        cls.loc_internal_a = cls.warehouse.lot_stock_id
        cls.loc_internal_b = cls.env['stock.location'].create({
            'name': 'Test Internal B',
            'usage': 'internal',
            'location_id': cls.warehouse.view_location_id.id,
        })
        cls.loc_supplier = cls.env.ref('stock.stock_location_suppliers')
        cls.loc_customer = cls.env.ref('stock.stock_location_customers')

        cls.parent_categ = cls.env['product.category'].create({'name': 'Report Parent Cat'})
        cls.child_categ = cls.env['product.category'].create({
            'name': 'Report Child Cat',
            'parent_id': cls.parent_categ.id,
        })
        cls.other_categ = cls.env['product.category'].create({'name': 'Report Other Cat'})

        cls.product_child = cls.env['product.product'].create({
            'name': 'Report Child Product',
            'is_storable': True,
            'categ_id': cls.child_categ.id,
        })
        cls.product_other = cls.env['product.product'].create({
            'name': 'Report Other Product',
            'is_storable': True,
            'categ_id': cls.other_categ.id,
        })
        cls.product_non_storable = cls.env['product.product'].create({
            'name': 'Report Non Storable',
            'is_storable': False,
            'categ_id': cls.child_categ.id,
        })

        cls.now = fields.Datetime.now()
        cls.past_date = cls.now - timedelta(days=5)
        cls.future_date = cls.now + timedelta(days=5)

        cls._create_done_move(cls.product_child, 10.0, cls.loc_supplier, cls.loc_internal_a, cls.past_date)
        cls._create_done_move(cls.product_child, 3.0, cls.loc_internal_a, cls.loc_internal_b, cls.past_date)
        cls._create_done_move(cls.product_other, 5.0, cls.loc_supplier, cls.loc_internal_a, cls.past_date)
        cls._create_done_move(cls.product_other, 5.0, cls.loc_internal_a, cls.loc_customer, cls.past_date)
        cls._create_done_move(cls.product_other, 4.0, cls.loc_supplier, cls.loc_internal_b, cls.future_date)
        cls._create_done_move(cls.product_non_storable, 8.0, cls.loc_supplier, cls.loc_internal_a, cls.past_date)

    @classmethod
    def _create_done_move(cls, product, qty, src, dest, move_date):
        move = cls.env['stock.move'].create({
            'product_id': product.id,
            'product_uom_qty': qty,
            'uom_id': product.uom_id.id,
            'location_id': src.id,
            'location_dest_id': dest.id,
        })
        move._action_confirm()
        move.quantity = qty
        move.picked = True
        move._action_done()
        move.write({'date': move_date})
        return move

    def test_get_report_values_with_category_and_date_filters(self):
        """Report values compute positive stock balances respecting category hierarchy and date."""
        data = {
            'category': [self.parent_categ.id],
            'location': [],
            'date': self.now,
            'loc_name': '',
            'categ_name': self.parent_categ.name,
            'inventory_date': self.now.strftime('%Y-%m-%d'),
        }
        res = self.report_model._get_report_values([], data)

        self.assertEqual(res['categ_name'], self.parent_categ.name)
        self.assertEqual(res['doc_quantities'], 0)
        self.assertEqual(res['inventory_date'], self.now.strftime('%Y-%m-%d'))

        balances = {
            (row['product'].id, row['location']): row['qty_available']
            for row in res['docs']
        }
        self.assertEqual(
            balances.get((self.product_child.id, self.loc_internal_a.complete_name)),
            7.0,
        )
        self.assertEqual(
            balances.get((self.product_child.id, self.loc_internal_b.complete_name)),
            3.0,
        )
        # Non-storable and other category products must be excluded
        product_ids = {row['product'].id for row in res['docs']}
        self.assertNotIn(self.product_other.id, product_ids)
        self.assertNotIn(self.product_non_storable.id, product_ids)

    def test_get_report_values_location_filter_and_zero_balance_excluded(self):
        """Location filter restricts balances to selected locations and omits zero balances."""
        data = {
            'category': [],
            'location': [self.loc_internal_b.id],
            'date': self.now,
            'loc_name': self.loc_internal_b.display_name,
            'categ_name': '',
            'inventory_date': self.now.strftime('%Y-%m-%d'),
        }
        res = self.report_model._get_report_values([], data)
        # Future move into loc_internal_b should be excluded at self.now
        self.assertEqual(len(res['docs']), 1)
        self.assertEqual(res['docs'][0]['product'], self.product_child)
        self.assertEqual(res['docs'][0]['qty_available'], 3.0)

        # At future_date without category filter, product_other in loc_internal_b appears,
        # while product_other in loc_internal_a (net 0) remains excluded.
        data_future = {
            'category': [],
            'location': [],
            'date': self.future_date,
            'loc_name': '',
            'categ_name': '',
            'inventory_date': self.future_date.strftime('%Y-%m-%d'),
        }
        res_future = self.report_model._get_report_values([], data_future)
        balances = {
            (row['product'].id, row['location']): row['qty_available']
            for row in res_future['docs']
        }
        self.assertNotIn((self.product_other.id, self.loc_internal_a.complete_name), balances)
        self.assertEqual(
            balances.get((self.product_other.id, self.loc_internal_b.complete_name)),
            4.0,
        )

