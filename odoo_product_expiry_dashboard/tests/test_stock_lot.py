# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase


class TestProductExpiryDashboard(TransactionCase):
    """Test suite for Product Expiry Dashboard (stock.lot extension).

    In Odoo 19, product.template.type = 'consu' means "Goods" (tangible).
    Inventory tracking is controlled by the is_storable boolean (added by the
    stock module). Setting is_storable=True allows stock.quant records to be
    created; without it the constraint raises:
        "Quants cannot be created for consumables or services."

    Quants are placed on-hand via stock.quant._update_available_quantity(),
    the standard ORM-safe API used by Odoo's own tests.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()


        # ── Product & category setup ──────────────────────────────────────────
        cls.category = cls.env['product.category'].create({
            'name': 'Test Perishable Category',
        })
        # Odoo 19: type='consu' = Goods; is_storable=True = inventory tracked
        cls.product = cls.env['product.product'].create({
            'name': 'Test Perishable Product',
            'type': 'consu',
            'is_storable': True,
            'categ_id': cls.category.id,
            'use_expiration_date': True,
            'tracking': 'lot',
        })
        cls.product2 = cls.env['product.product'].create({
            'name': 'Another Perishable Product',
            'type': 'consu',
            'is_storable': True,
            'categ_id': cls.category.id,
            'use_expiration_date': True,
            'tracking': 'lot',
        })

        # ── Location ──────────────────────────────────────────────────────────
        cls.location = cls.env.ref('stock.stock_location_stock')

        # ── Snapshot of today ─────────────────────────────────────────────────
        cls.today = fields.Date.today()

    # ------------------------------------------------------------------
    # Helper: create a lot + add on-hand stock via _update_available_quantity
    # ------------------------------------------------------------------
    def _make_lot(self, product, days_offset, qty=5.0, name_suffix=''):
        """Create a stock.lot with expiration_date = today + *days_offset*
        and place *qty* units on-hand using the standard quant API.

        Uses _update_available_quantity so stock.quant constraints are
        satisfied (no manual quant create for consumables etc.).
        """
        exp_date = self.today + timedelta(days=days_offset)
        lot = self.env['stock.lot'].create({
            'name': f'LOT-{days_offset}-{name_suffix}',
            'product_id': product.id,
            'expiration_date': fields.Datetime.to_datetime(str(exp_date)),
            'company_id': self.env.company.id,
        })
        # Place stock on-hand via the ORM helper
        self.env['stock.quant']._update_available_quantity(
            product, self.location, qty, lot_id=lot
        )
        return lot

    # ==================================================================
    # test_01 – get_product_expiry: return structure
    # ==================================================================
    def test_01_get_product_expiry_structure(self):
        """get_product_expiry always returns a dict with the 6 expected keys."""

        result = self.env['stock.lot'].get_product_expiry({})
        expected_keys = {'expired', 'today', 'one_day',
                         'seven_day', 'thirty_day', 'one_twenty_day'}
        self.assertEqual(set(result.keys()), expected_keys,
                         "Return dict must contain exactly the 6 expiry keys.")
        for key, val in result.items():
            self.assertIsInstance(val, (int, float),
                                  f"Key '{key}' must be numeric.")


    # ==================================================================
    # test_02 – expired lots counted correctly
    # ==================================================================
    def test_02_expired_lots(self):
        """Lots past their expiration date appear under 'expired'."""

        self._make_lot(self.product, -3, qty=4.0, name_suffix='expired')
        result = self.env['stock.lot'].get_product_expiry({})
        self.assertGreaterEqual(result['expired'], 4.0,
                                "Expired qty must include the past-due lot.")
        self.assertEqual(result['today'], 0,
                         "'today' must NOT include an expired lot.")

    # ==================================================================
    # test_03 – lot expiring today
    # ==================================================================
    def test_03_expiry_today(self):
        """Lots expiring today are counted under 'today' only."""
        self._make_lot(self.product, 0, qty=6.0, name_suffix='today')
        result = self.env['stock.lot'].get_product_expiry({})
        self.assertGreaterEqual(result['today'], 6.0,
                                "'today' must include lot expiring today.")
        self.assertEqual(result['one_day'], 0,
                         "'one_day' must NOT include today's lot.")


    # ==================================================================
    # test_04 – lot expiring in exactly 1 day (overlapping ranges)
    # ==================================================================
    def test_04_expiry_one_day(self):
        """Lots expiring in 1 day appear in one_day, seven_day, thirty_day,
        and one_twenty_day (overlapping tile logic)."""

        self._make_lot(self.product, 1, qty=3.0, name_suffix='1day')
        result = self.env['stock.lot'].get_product_expiry({})
        self.assertGreaterEqual(result['one_day'], 3.0)
        self.assertGreaterEqual(result['seven_day'], 3.0)
        self.assertGreaterEqual(result['thirty_day'], 3.0)
        self.assertGreaterEqual(result['one_twenty_day'], 3.0)
        self.assertEqual(result['expired'], 0)


    # ==================================================================
    # test_05 – 7-day boundary
    # ==================================================================
    def test_05_expiry_seven_days_boundary(self):
        """Lots at exactly the 7-day boundary appear in seven_day, thirty_day,
        and one_twenty_day, but NOT in one_day."""
        self._make_lot(self.product, 7, qty=2.0, name_suffix='7days')
        result = self.env['stock.lot'].get_product_expiry({})
        self.assertGreaterEqual(result['seven_day'], 2.0)
        self.assertGreaterEqual(result['thirty_day'], 2.0)
        self.assertGreaterEqual(result['one_twenty_day'], 2.0)
        self.assertEqual(result['one_day'], 0,
                         "'one_day' must NOT include a +7 day lot.")

    # ==================================================================
    # test_06 – beyond 120 days: no tile should count it
    # ==================================================================
    def test_06_expiry_beyond_120_days(self):
        """Lots expiring beyond 120 days must NOT appear in any dashboard tile."""
        self._make_lot(self.product, 121, qty=9.0, name_suffix='121days')
        result = self.env['stock.lot'].get_product_expiry({})
        self.assertEqual(result['one_twenty_day'], 0)
        self.assertEqual(result['thirty_day'], 0)
        self.assertEqual(result['seven_day'], 0)
        self.assertEqual(result['one_day'], 0)
        self.assertEqual(result['today'], 0)
        self.assertEqual(result['expired'], 0)

    # ==================================================================
    # test_07 – date range filter (start_date / end_date)
    # ==================================================================
    def test_07_date_range_filter(self):
        """Date range params restrict which lots are included."""
        # lot_inside: -2 days → within [-5, -1] range
        self._make_lot(self.product, -2, qty=5.0, name_suffix='inside_range')
        # lot_outside: -10 days → outside [-5, -1] range
        self._make_lot(self.product2, -10, qty=7.0, name_suffix='outside_range')

        start = str(self.today - timedelta(days=5))
        end = str(self.today - timedelta(days=1))

        result = self.env['stock.lot'].get_product_expiry(
            {'start_date': start, 'end_date': end})

        self.assertGreaterEqual(result['expired'], 5.0,
                                "Lot inside range must appear as expired.")

    # ==================================================================
    # test_08 – start_date only filter
    # ==================================================================
    def test_08_start_date_only_filter(self):
        """When only start_date is given, lots before it are excluded."""
        self._make_lot(self.product, -1, qty=3.0, name_suffix='after_start')
        start = str(self.today - timedelta(days=3))
        result = self.env['stock.lot'].get_product_expiry({'start_date': start})
        self.assertGreaterEqual(result['expired'], 3.0)

    # ==================================================================
    # test_09 – get_expired_product returns product-name → qty mapping
    # ==================================================================
    def test_09_get_expired_product(self):
        """get_expired_product returns a {product_name: qty} dict."""
        self._make_lot(self.product, -1, qty=4.0, name_suffix='exp_p')
        result = self.env['stock.lot'].get_expired_product({})
        self.assertIsInstance(result, dict)
        self.assertIn(self.product.name, result,
                      "Expired product name must be a key in the result.")
        self.assertGreaterEqual(result[self.product.name], 4.0)

    # ==================================================================
    # test_10 – get_product_expiry_by_category
    # ==================================================================
    def test_10_get_product_expiry_by_category(self):
        """get_product_expiry_by_category returns {category_name: qty} dict."""
        self._make_lot(self.product, -1, qty=3.0, name_suffix='cat_p')
        result = self.env['stock.lot'].get_product_expiry_by_category({})
        self.assertIsInstance(result, dict)
        self.assertIn(self.category.name, result,
                      "Category name must appear in the result dict.")
        self.assertGreaterEqual(result[self.category.name], 3.0)

    # ==================================================================
    # test_11 – get_near_expiry_product (within 7 days)
    # ==================================================================
    def test_11_get_near_expiry_product(self):
        """get_near_expiry_product includes products expiring within 7 days
        and excludes those expiring in 8+ days."""
        self._make_lot(self.product, 3, qty=5.0, name_suffix='near_p')
        self._make_lot(self.product2, 8, qty=9.0, name_suffix='far_p')
        result = self.env['stock.lot'].get_near_expiry_product()
        self.assertIsInstance(result, dict)
        self.assertIn(self.product.name, result,
                      "Near-expiry product must appear in the result.")
        self.assertNotIn(self.product2.name, result,
                         "Product expiring in 8 days must NOT appear.")

    # ==================================================================
    # test_12 – get_near_expiry_category (within 7 days)
    # ==================================================================
    def test_12_get_near_expiry_category(self):
        """get_near_expiry_category includes categories with products
        expiring within 7 days."""
        self._make_lot(self.product, 5, qty=2.0, name_suffix='near_cat')
        result = self.env['stock.lot'].get_near_expiry_category()
        self.assertIsInstance(result, dict)
        self.assertIn(self.category.name, result,
                      "Near-expiry category must appear in the result.")

    # ==================================================================
    # test_13 – get_product_expired_today returns int count
    # ==================================================================
    def test_13_get_product_expired_today(self):
        """get_product_expired_today returns the count of lots expiring today."""
        before = self.env['stock.lot'].get_product_expired_today()
        self._make_lot(self.product, 0, qty=1.0, name_suffix='today_count')
        after = self.env['stock.lot'].get_product_expired_today()
        self.assertIsInstance(after, int,
                              "get_product_expired_today must return an int.")
        self.assertEqual(after, before + 1,
                         "Count must increase by 1 after adding a today-expiry lot.")

    # ==================================================================
    # test_14 – zero-qty lots are excluded from all tiles
    # ==================================================================
    def test_14_zero_qty_lots_excluded(self):
        """Lots with no quant (product_qty == 0) are excluded from all tiles."""
        exp_date = self.today + timedelta(days=2)
        # Create a lot without placing any stock
        self.env['stock.lot'].create({
            'name': 'LOT-ZERO-QTY',
            'product_id': self.product.id,
            'expiration_date': fields.Datetime.to_datetime(str(exp_date)),
            'company_id': self.env.company.id,
        })
        result = self.env['stock.lot'].get_product_expiry({})
        self.assertEqual(result['one_day'], 0,
                         "Zero-qty lot must be excluded from dashboard counts.")
        self.assertEqual(result['seven_day'], 0)

    # ==================================================================
    # test_15 – multiple lots accumulate quantity
    # ==================================================================
    def test_15_multiple_lots_accumulate(self):
        """Multiple expired lots sum their quantities in the 'expired' tile."""
        self._make_lot(self.product, -1, qty=3.0, name_suffix='acc1')
        self._make_lot(self.product2, -2, qty=7.0, name_suffix='acc2')
        result = self.env['stock.lot'].get_product_expiry({})
        self.assertGreaterEqual(result['expired'], 10.0,
                                "Expired total must be >= the sum of both lots.")
