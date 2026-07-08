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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductTemplate(TransactionCase):
    """Test cases for product.template._onchange_product_measures defined in
    product_volume/models/product_template.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].new({
            'name': 'Volume Test Product',
            'length_uom': 'meters',
            'volume_uom': 'cubic_meters',
        })

    # -----------------------------------------------------------------
    # Tests for _onchange_product_measures
    # -----------------------------------------------------------------

    def test_onchange_product_measures_meters_cubic_meters(self):
        """When length_uom='meters' and volume_uom='cubic_meters', volume must
        equal length × breadth × height (no unit conversion factor)."""
        self.product.length = '3'
        self.product.breadth = '2'
        self.product.height = '4'
        self.product.length_uom = 'meters'
        self.product.volume_uom = 'cubic_meters'
        self.product._onchange_product_measures()
        self.assertAlmostEqual(
            self.product.volume, 24.0, places=4,
            msg="Volume (meters, cubic_meters) should be 3×2×4 = 24.0 m³."
        )

    def test_onchange_product_measures_meters_cubic_feet(self):
        """When length_uom='meters' and volume_uom='cubic_feet', volume in cubic
        metres must be converted to cubic feet by multiplying by 35.3147."""
        self.product.length = '2'
        self.product.breadth = '2'
        self.product.height = '2'
        self.product.length_uom = 'meters'
        self.product.volume_uom = 'cubic_feet'
        self.product._onchange_product_measures()
        expected = 8.0 * 35.3147
        self.assertAlmostEqual(
            self.product.volume, expected, places=2,
            msg=f"Volume (meters, cubic_feet) should be 8 × 35.3147 = {expected}."
        )

    def test_onchange_product_measures_meters_cubic_inches(self):
        """When length_uom='meters' and volume_uom='cubic_inches', volume in cubic
        metres must be converted to cubic inches by multiplying by 61023.7."""
        self.product.length = '1'
        self.product.breadth = '1'
        self.product.height = '1'
        self.product.length_uom = 'meters'
        self.product.volume_uom = 'cubic_inches'
        self.product._onchange_product_measures()
        expected = 1.0 * 61023.7
        self.assertAlmostEqual(
            self.product.volume, expected, places=1,
            msg=f"Volume (meters, cubic_inches) should be 1 × 61023.7 = {expected}."
        )

    def test_onchange_product_measures_meters_cubic_yards(self):
        """When length_uom='meters' and volume_uom='cubic_yards', volume in cubic
        metres must be converted to cubic yards by multiplying by 1.308."""
        self.product.length = '3'
        self.product.breadth = '3'
        self.product.height = '3'
        self.product.length_uom = 'meters'
        self.product.volume_uom = 'cubic_yards'
        self.product._onchange_product_measures()
        expected = 27.0 * 1.308
        self.assertAlmostEqual(
            self.product.volume, expected, places=2,
            msg=f"Volume (meters, cubic_yards) should be 27 × 1.308 = {expected}."
        )

    def test_onchange_product_measures_centimeters(self):
        """When length_uom='centimeters', volume must be divided by 1,000,000
        to convert cm³ to m³ before applying the volume_uom conversion."""
        self.product.length = '100'
        self.product.breadth = '100'
        self.product.height = '100'
        self.product.length_uom = 'centimeters'
        self.product.volume_uom = 'cubic_meters'
        self.product._onchange_product_measures()
        # 100×100×100 cm³ = 1,000,000 cm³ → / 1,000,000 = 1 m³
        self.assertAlmostEqual(
            self.product.volume, 1.0, places=4,
            msg="Volume (centimeters, cubic_meters): 100×100×100 / 1e6 = 1.0 m³."
        )

    def test_onchange_product_measures_inches(self):
        """When length_uom='inches', volume must be divided by 61023.7 to
        convert cubic inches to m³ before applying the volume_uom conversion."""
        self.product.length = '10'
        self.product.breadth = '10'
        self.product.height = '10'
        self.product.length_uom = 'inches'
        self.product.volume_uom = 'cubic_meters'
        self.product._onchange_product_measures()
        expected = 1000 / 61023.7
        self.assertAlmostEqual(
            self.product.volume, expected, places=2,
            msg=f"Volume (inches, cubic_meters): 10³ / 61023.7 = {expected}."
        )

    def test_onchange_product_measures_feet(self):
        """When length_uom='feet', volume must be divided by 35.3147 to
        convert cubic feet to m³ before applying the volume_uom conversion."""
        self.product.length = '5'
        self.product.breadth = '5'
        self.product.height = '5'
        self.product.length_uom = 'feet'
        self.product.volume_uom = 'cubic_meters'
        self.product._onchange_product_measures()
        expected = 125 / 35.3147
        self.assertAlmostEqual(
            self.product.volume, expected, places=2,
            msg=f"Volume (feet, cubic_meters): 5³ / 35.3147 = {expected}."
        )

    def test_onchange_product_measures_yards(self):
        """When length_uom='yards', volume must be divided by 1.308 to convert
        cubic yards to m³ before applying the volume_uom conversion."""
        self.product.length = '2'
        self.product.breadth = '2'
        self.product.height = '2'
        self.product.length_uom = 'yards'
        self.product.volume_uom = 'cubic_meters'
        self.product._onchange_product_measures()
        expected = 8 / 1.308
        self.assertAlmostEqual(
            self.product.volume, expected, places=2,
            msg=f"Volume (yards, cubic_meters): 8 / 1.308 = {expected}."
        )

    def test_onchange_product_measures_zero_dimensions(self):
        """When all dimensions are empty/zero, volume must be 0 regardless of
        the selected UoM."""
        self.product.length = ''
        self.product.breadth = ''
        self.product.height = ''
        self.product.length_uom = 'meters'
        self.product.volume_uom = 'cubic_meters'
        self.product._onchange_product_measures()
        self.assertEqual(
            self.product.volume, 0,
            "Volume must be 0 when all dimensions are empty."
        )

    def test_onchange_product_measures_partial_dimensions_return_zero(self):
        """When only some dimensions are provided (e.g., length only), the
        missing dimensions default to 0, making volume 0."""
        self.product.length = '5'
        self.product.breadth = ''
        self.product.height = ''
        self.product.length_uom = 'meters'
        self.product.volume_uom = 'cubic_meters'
        self.product._onchange_product_measures()
        self.assertEqual(
            self.product.volume, 0,
            "Volume must be 0 when breadth or height are missing."
        )
