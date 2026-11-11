# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install')
class TestInventoryMoveMiniDashboard(TransactionCase):
    """Test dashboard data retrieval for stock moves and pickings."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StockMove = cls.env['stock.move']
        cls.StockPicking = cls.env['stock.picking']

    def test_stock_move_dashboard(self):
        """Test retrieve_inventory_dashboard method returns valid data and keys."""
        data = self.StockMove.retrieve_inventory_dashboard()
        expected_keys = {
            'draft', 'waiting', 'assigned', 'done',
            'count', 'average_products'
        }
        self.assertEqual(set(data.keys()), expected_keys)
        self.assertIsInstance(data['count'], int)
        self.assertIsInstance(data['average_products'], int)

    def test_stock_picking_dashboard(self):
        """Test stock_picking_dashboard method returns valid data and keys."""
        data = self.StockPicking.stock_picking_dashboard()
        expected_keys = {
            'draft', 'waiting', 'assigned', 'done',
            'receipts', 'outgoing', 'internal', 'cancel'
        }
        self.assertTrue(expected_keys.issubset(data.keys()))
        self.assertIsInstance(data['receipts'], int)
        self.assertIsInstance(data['outgoing'], int)
        self.assertIsInstance(data['internal'], int)
        self.assertIsInstance(data['cancel'], int)

