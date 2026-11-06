# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aleena K (odoo@cybrosys.com)
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
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestProductBarcode(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Demo Machine',
        })

    def test_check_ean_valid(self):
        """Test valid EAN."""
        result = self.product.check_ean(
            '1234567890128'
        )
        self.assertIsInstance(
            result,
            int
        )

    def test_check_ean_invalid(self):
        """Test invalid EAN."""
        result = self.product.check_ean(
            '123'
        )
        self.assertFalse(result)

    def test_ean_checksum(self):
        """Test EAN checksum."""
        result = self.product.ean_checksum(
            '1234567890128'
        )
        self.assertIsInstance(
            result,
            int
        )

    def test_generate_ean(self):
        """Test EAN generation."""
        ean = self.product.generate_ean()
        self.assertEqual(
            len(ean),
            13
        )

    def test_action_generate_barcode(self):
        """Test barcode generation action."""
        self.product.action_generate_barcode()
        self.assertTrue(
            self.product.barcode
        )
        self.assertEqual(
            len(self.product.barcode),
            13
        )
