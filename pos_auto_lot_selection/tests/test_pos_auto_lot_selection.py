# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin k(odoo@cybrosys.com)
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
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo import fields

class TestPosAutoLotSelection(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a test stock location
        cls.stock_location = cls.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
        })
        # Create a product category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })
        # Create a tracked product
        cls.product = cls.env['product.product'].create({
            'name': 'Test Tracked Product',
            'is_storable': True,
            'tracking': 'lot',
            'categ_id': cls.category.id,
        })

    def test_default_removal_strategy_fifo(self):
        """ Test that when category removal strategy is default/FIFO (create_date asc),
            the older lot is selected and marked as taken. """
        # Create two lots
        lot_first = self.env['stock.lot'].create({
            'name': 'LOT-FIRST',
            'product_id': self.product.id,
        })
        lot_second = self.env['stock.lot'].create({
            'name': 'LOT-SECOND',
            'product_id': self.product.id,
        })

        # Set lot_first's create_date to be 1 day in the past using SQL to make it deterministic
        self.env.cr.execute(
            "UPDATE stock_lot SET create_date = %s WHERE id = %s",
            (datetime.now() - timedelta(days=1), lot_first.id)
        )
        # Clear env cache for lot_first so Odoo reads the updated create_date
        lot_first.invalidate_recordset(['create_date'])

        # Set positive quantities for both lots
        self.env['stock.quant'].with_context(inventory_mode=True).create([
            {
                'product_id': self.product.id,
                'location_id': self.stock_location.id,
                'lot_id': lot_first.id,
                'quantity': 10,
            },
            {
                'product_id': self.product.id,
                'location_id': self.stock_location.id,
                'lot_id': lot_second.id,
                'quantity': 10,
            }
        ])

        # Get available lots for POS
        selected_lots = self.env['stock.lot'].get_available_lots_for_pos(self.product.id)

        # Assertions
        self.assertEqual(selected_lots, ['LOT-FIRST'])
        self.assertTrue(lot_first.is_taken)
        self.assertFalse(lot_second.is_taken)

    def test_fefo_removal_strategy(self):
        """ Test that when category removal strategy is FEFO, the lot with the earliest
            expiration date is selected first. """
        # Search or create a FEFO removal strategy
        fefo_strategy = self.env['product.removal'].search([('method', '=', 'fefo')], limit=1)
        if not fefo_strategy:
            fefo_strategy = self.env['product.removal'].create({
                'name': 'First Expiry First Out (FEFO)',
                'method': 'fefo',
            })
        
        # Set category removal strategy to FEFO
        self.category.removal_strategy_id = fefo_strategy.id

        # Create two lots: lot_expiring_soon and lot_expiring_later
        # We create lot_expiring_later first (earlier create_date/id) but with a later expiration_date
        lot_expiring_later = self.env['stock.lot'].create({
            'name': 'LOT-EXP-LATER',
            'product_id': self.product.id,
            'expiration_date': fields.Datetime.now() + timedelta(days=30),
        })
        lot_expiring_soon = self.env['stock.lot'].create({
            'name': 'LOT-EXP-SOON',
            'product_id': self.product.id,
            'expiration_date': fields.Datetime.now() + timedelta(days=5),
        })

        # Set positive quantities for both lots
        self.env['stock.quant'].with_context(inventory_mode=True).create([
            {
                'product_id': self.product.id,
                'location_id': self.stock_location.id,
                'lot_id': lot_expiring_later.id,
                'quantity': 10,
            },
            {
                'product_id': self.product.id,
                'location_id': self.stock_location.id,
                'lot_id': lot_expiring_soon.id,
                'quantity': 10,
            }
        ])

        # Get available lots for POS
        selected_lots = self.env['stock.lot'].get_available_lots_for_pos(self.product.id)

        # Assertions
        self.assertEqual(selected_lots, ['LOT-EXP-SOON'])
        self.assertTrue(lot_expiring_soon.is_taken)
        self.assertFalse(lot_expiring_later.is_taken)

    def test_no_lots_available(self):
        """ Test that when no lots have quantities available, it returns an empty list
            and no lot's is_taken field is modified. """
        # Create a lot but don't add quantity (quant is 0)
        lot_empty = self.env['stock.lot'].create({
            'name': 'LOT-EMPTY',
            'product_id': self.product.id,
        })

        # Get available lots for POS
        selected_lots = self.env['stock.lot'].get_available_lots_for_pos(self.product.id)

        # Assertions
        self.assertEqual(selected_lots, [])
        self.assertFalse(lot_empty.is_taken)
