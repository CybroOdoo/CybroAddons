# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.tests import tagged
from odoo.fields import Datetime
from datetime import timedelta


@tagged('post_install', '-at_install')
class TestPosAutoLotSelection(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPosAutoLotSelection, cls).setUpClass()

        # Create a product with tracking enabled
        cls.product = cls.env['product.product'].create({
            'name': 'POS Tracked Product',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'lot',
        })

        # Find or create a stock location for updating quants
        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.env.company.id)
        ], limit=1)
        if cls.warehouse:
            cls.stock_location = cls.warehouse.lot_stock_id
        else:
            cls.stock_location = cls.env['stock.location'].search([
                ('usage', '=', 'internal')
            ], limit=1)

    def _add_quantity_to_lot(self, lot, qty):
        """Helper to set quantity for a lot using stock.quant."""
        self.env['stock.quant'].create({
            'product_id': self.product.id,
            'location_id': self.stock_location.id,
            'lot_id': lot.id,
            'quantity': qty,
            'company_id': self.env.company.id,
        })

    def test_get_available_lots_for_pos_no_lots(self):
        """Test that get_available_lots_for_pos returns empty list if no lots exist."""
        # Create a new tracked product with no lots
        new_product = self.env['product.product'].create({
            'name': 'Another Tracked Product',
            'type': 'consu',
            'is_storable': True,
            'tracking': 'lot',
        })
        res = self.env['stock.lot'].get_available_lots_for_pos(new_product.id)
        self.assertEqual(res, [], "Should return empty list when no lots exist")

    def test_get_available_lots_for_pos_no_qty(self):
        """Test that lots with no quantity available are not selected."""
        self.env['stock.lot'].create({
            'name': 'LOT-NO-QTY',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
        })
        res = self.env['stock.lot'].get_available_lots_for_pos(self.product.id)
        self.assertEqual(res, [], "Should return empty list when lot has no quantity")

    def test_get_available_lots_for_pos_fefo_priority(self):
        """Test FEFO (First Expired, First Out) ordering. Earliest expiration_date should be selected."""
        # Create lot 1: expiring in 10 days
        lot_far = self.env['stock.lot'].create({
            'name': 'LOT-EXP-FAR',
            'product_id': self.product.id,
            'expiration_date': Datetime.now() + timedelta(days=10),
            'company_id': self.env.company.id,
        })
        # Create lot 2: expiring in 2 days (soonest)
        lot_soon = self.env['stock.lot'].create({
            'name': 'LOT-EXP-SOON',
            'product_id': self.product.id,
            'expiration_date': Datetime.now() + timedelta(days=2),
            'company_id': self.env.company.id,
        })
        # Create lot 3: expiring in 5 days
        lot_mid = self.env['stock.lot'].create({
            'name': 'LOT-EXP-MID',
            'product_id': self.product.id,
            'expiration_date': Datetime.now() + timedelta(days=5),
            'company_id': self.env.company.id,
        })

        # Add quantity to all lots
        self._add_quantity_to_lot(lot_far, 10.0)
        self._add_quantity_to_lot(lot_soon, 10.0)
        self._add_quantity_to_lot(lot_mid, 10.0)

        # Call the auto lot selection
        res = self.env['stock.lot'].get_available_lots_for_pos(self.product.id)

        # It should select the one expiring soonest
        self.assertEqual(res, [lot_soon.name], "Should select the lot with the earliest expiration date")
        self.assertTrue(lot_soon.is_taken, "Selected lot should be marked as taken")
        self.assertFalse(lot_far.is_taken, "Other lots should not be marked as taken")
        self.assertFalse(lot_mid.is_taken, "Other lots should not be marked as taken")

    def test_get_available_lots_for_pos_create_date_fallback(self):
        """Test fallback ordering based on create_date/creation order when expiration dates are not set."""
        # Create lot 1 (oldest)
        lot_old = self.env['stock.lot'].create({
            'name': 'LOT-OLD',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
        })
        # Create lot 2 (newest)
        lot_new = self.env['stock.lot'].create({
            'name': 'LOT-NEW',
            'product_id': self.product.id,
            'company_id': self.env.company.id,
        })

        # Add quantity to both
        self._add_quantity_to_lot(lot_old, 5.0)
        self._add_quantity_to_lot(lot_new, 5.0)

        # Call auto selection
        res = self.env['stock.lot'].get_available_lots_for_pos(self.product.id)

        # It should select the oldest one by creation order
        self.assertEqual(res, [lot_old.name], "Should select the oldest lot when expiration date is not present")
        self.assertTrue(lot_old.is_taken, "Selected lot should be marked as taken")
        self.assertFalse(lot_new.is_taken, "Newer lot should not be marked as taken")
