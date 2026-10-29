# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLotExpiryCheck(TransactionCase):
    """Tests for ``product.product.lot_expiry_check``.

    The method returns:
        * ``0``                    -> the lot does not exist for the product
        * ``[2, expiration_date]`` -> the lot has expired
        * ``[1, expiration_date]`` -> the alert date has passed (expires soon)
        * ``1``                    -> the lot is valid
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.now = fields.Datetime.now()
        cls.product = cls.env['product.product'].create({
            'name': 'Expiry Test Product',
            'is_storable': True,
            'tracking': 'lot',
            'use_expiration_date': True,
        })
        cls.other_product = cls.env['product.product'].create({
            'name': 'Expiry Test Other Product',
            'is_storable': True,
            'tracking': 'lot',
            'use_expiration_date': True,
        })
        cls.lot_expired = cls._create_lot(
            'LOT-EXPIRED', cls.product,
            expiration_date=cls.now - timedelta(days=2),
            alert_date=cls.now - timedelta(days=10))
        cls.lot_alert = cls._create_lot(
            'LOT-ALERT', cls.product,
            expiration_date=cls.now + timedelta(days=5),
            alert_date=cls.now - timedelta(days=1))
        cls.lot_valid = cls._create_lot(
            'LOT-VALID', cls.product,
            expiration_date=cls.now + timedelta(days=30),
            alert_date=cls.now + timedelta(days=20))
        cls.lot_no_dates = cls._create_lot('LOT-NO-DATES', cls.product)

    @classmethod
    def _create_lot(cls, name, product, expiration_date=False, alert_date=False):
        lot = cls.env['stock.lot'].create({
            'name': name,
            'product_id': product.id,
            'company_id': cls.env.company.id,
        })
        # Written after creation so the product_expiry computed defaults
        # cannot override the dates used by the tests.
        lot.write({
            'expiration_date': expiration_date,
            'alert_date': alert_date,
        })
        return lot

    def _check(self, product, lot_name):
        return self.env['product.product'].lot_expiry_check(product.id, lot_name)

    def test_lot_does_not_exist(self):
        """An unknown lot name returns 0."""
        self.assertEqual(self._check(self.product, 'LOT-DOES-NOT-EXIST'), 0)

    def test_lot_belongs_to_another_product(self):
        """A lot that exists only for another product is treated as missing."""
        self._create_lot('LOT-OTHER-ONLY', self.other_product)
        self.assertEqual(self._check(self.product, 'LOT-OTHER-ONLY'), 0)

    def test_same_lot_name_on_two_products(self):
        """The same lot name on two products is resolved per product."""
        self._create_lot(
            'LOT-SHARED', self.other_product,
            expiration_date=self.now - timedelta(days=1))
        self._create_lot(
            'LOT-SHARED', self.product,
            expiration_date=self.now + timedelta(days=30))
        self.assertEqual(self._check(self.product, 'LOT-SHARED'), 1)
        self.assertEqual(self._check(self.other_product, 'LOT-SHARED')[0], 2)

    def test_expired_lot(self):
        """An expired lot returns [2, expiration_date]."""
        result = self._check(self.product, 'LOT-EXPIRED')
        self.assertEqual(result[0], 2)
        self.assertEqual(result[1], self.lot_expired.expiration_date)

    def test_expired_takes_precedence_over_alert(self):
        """LOT-EXPIRED has both dates in the past: expiry wins over the alert."""
        self.assertLessEqual(self.lot_expired.alert_date, self.now)
        self.assertEqual(self._check(self.product, 'LOT-EXPIRED')[0], 2)

    def test_alert_lot(self):
        """A lot past its alert date, but not expired, returns [1, expiration_date]."""
        result = self._check(self.product, 'LOT-ALERT')
        self.assertEqual(result[0], 1)
        self.assertEqual(result[1], self.lot_alert.expiration_date)

    def test_valid_lot(self):
        """A lot with both dates in the future returns 1."""
        self.assertEqual(self._check(self.product, 'LOT-VALID'), 1)

    def test_lot_without_dates(self):
        """A lot without expiration or alert date is valid."""
        self.assertEqual(self._check(self.product, 'LOT-NO-DATES'), 1)

    def test_lot_with_only_expiration_date(self):
        """A future expiration date without an alert date is valid."""
        self._create_lot(
            'LOT-ONLY-EXPIRATION', self.product,
            expiration_date=self.now + timedelta(days=3))
        self.assertEqual(self._check(self.product, 'LOT-ONLY-EXPIRATION'), 1)

    def test_lot_with_only_alert_date_passed(self):
        """A passed alert date without an expiration date returns the alert code."""
        self._create_lot(
            'LOT-ONLY-ALERT', self.product,
            alert_date=self.now - timedelta(days=1))
        result = self._check(self.product, 'LOT-ONLY-ALERT')
        self.assertEqual(result[0], 1)
        self.assertFalse(result[1])

    def test_expiration_date_equal_to_now_is_expired(self):
        """A lot that expires exactly 'now' is already considered expired."""
        fixed_now = fields.Datetime.now()
        lot = self._create_lot(
            'LOT-BOUNDARY', self.product, expiration_date=fixed_now)
        with patch.object(fields.Datetime, 'now', return_value=fixed_now):
            result = self._check(self.product, lot.name)
        self.assertEqual(result[0], 2)

    def test_result_changes_when_dates_change(self):
        """Updating the lot dates is reflected on the next check."""
        lot = self._create_lot(
            'LOT-CHANGING', self.product,
            expiration_date=self.now + timedelta(days=30))
        self.assertEqual(self._check(self.product, lot.name), 1)
        lot.expiration_date = self.now - timedelta(days=1)
        self.assertEqual(self._check(self.product, lot.name)[0], 2)
