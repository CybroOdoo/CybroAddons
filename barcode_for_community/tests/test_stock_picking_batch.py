# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase

class TestStockPickingBatch(TransactionCase):
    """Test suite for validating custom stock picking batch operation behavior."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and initialize dependencies if installed."""
        super(TestStockPickingBatch, cls).setUpClass()
        if 'stock.picking.batch' not in cls.env:
            cls.skipTest(cls, 'stock_picking_batch module not installed')
        
    def test_open_batch_record(self):
        """Test get the open batch action dict"""
        batch = self.env['stock.picking.batch'].create({
            'name': 'Test Batch'
        })
        action = batch.open_batch_record()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'custom_batch_lines_client_action')
