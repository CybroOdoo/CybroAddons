#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
"""Test suite for product dimensions and volume calculation."""
from odoo.tests.common import TransactionCase, tagged



@tagged('post_install', '-at_install')
class TestProductVolume(TransactionCase):
    """Unit tests for product dimensions and volume calculation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Volume Product',
            'type': 'consu',
        })

    def test_volume_calculation_meters(self):
        """Test volume calculation with length in meters."""
        self.product_template.write({
            'length': 2.0,
            'breadth': 3.0,
            'height': 4.0,
            'length_uom': 'meters',
        })
        self.assertAlmostEqual(self.product_template.volume, 24.0, places=2)
        self.assertAlmostEqual(
            self.product_template.calc_volume, 24.0, places=2
        )
        self.assertAlmostEqual(
            self.product_template.product_variant_ids.volume, 24.0, places=2
        )

    def test_volume_calculation_centimeters(self):
        """Test volume calculation with length in centimeters."""
        self.product_template.write({
            'length': 100.0,
            'breadth': 100.0,
            'height': 100.0,
            'length_uom': 'centimeters',
        })
        self.assertAlmostEqual(self.product_template.volume, 1.0, places=2)
        self.assertAlmostEqual(
            self.product_template.calc_volume, 1.0, places=2
        )

    def test_volume_calculation_inches(self):
        """Test volume calculation with length in inches."""
        self.product_template.write({
            'length': 10.0,
            'breadth': 10.0,
            'height': 10.0,
            'length_uom': 'inches',
        })
        expected_volume = 1000.0 / 61023.7
        self.assertAlmostEqual(
            self.product_template.volume, expected_volume, places=2
        )
        self.assertAlmostEqual(
            self.product_template.calc_volume, expected_volume, places=2
        )

    def test_volume_calculation_feet(self):
        """Test volume calculation with length in feet."""
        self.product_template.write({
            'length': 3.0,
            'breadth': 2.0,
            'height': 2.0,
            'length_uom': 'feet',
        })
        expected_volume = 12.0 / 35.3147
        self.assertAlmostEqual(
            self.product_template.volume, expected_volume, places=2
        )

    def test_volume_calculation_yards(self):
        """Test volume calculation with length in yards."""
        self.product_template.write({
            'length': 2.0,
            'breadth': 2.0,
            'height': 2.0,
            'length_uom': 'yards',
        })
        expected_volume = 8.0 / 1.308
        self.assertAlmostEqual(
            self.product_template.volume, expected_volume, places=2
        )

    def test_volume_api_create(self):
        """Test volume calculation when created via ORM/API create."""
        product = self.env['product.template'].create({
            'name': 'API Created Product',
            'length': 1.0,
            'breadth': 2.0,
            'height': 3.0,
            'length_uom': 'meters',
        })
        self.assertAlmostEqual(product.volume, 6.0, places=2)
        self.assertAlmostEqual(product.calc_volume, 6.0, places=2)
        self.assertAlmostEqual(
            product.product_variant_ids.volume, 6.0, places=2
        )

    def test_volume_compute_update(self):
        """Test compute trigger when dimensions are updated."""
        self.product_template.write({
            'length': 5.0,
            'breadth': 2.0,
            'height': 3.0,
            'length_uom': 'meters',
        })
        self.assertAlmostEqual(self.product_template.volume, 30.0, places=2)
        self.assertAlmostEqual(
            self.product_template.calc_volume, 30.0, places=2
        )

    def test_zero_dimensions(self):
        """Test that zero dimensions produce 0 volume."""
        self.product_template.write({
            'length': 0.0,
            'breadth': 5.0,
            'height': 5.0,
            'length_uom': 'meters',
        })
        self.assertEqual(self.product_template.volume, 0.0)
        self.assertEqual(self.product_template.calc_volume, 0.0)

    def test_volume_screenshot_case(self):
        """Test the case from screenshot (10 x 5 x 4 meters = 200 m3)."""
        self.product_template.write({
            'length': 10.0,
            'breadth': 5.0,
            'height': 4.0,
            'length_uom': 'meters',
            'volume_uom': 'cubic_meters',
        })
        self.assertAlmostEqual(self.product_template.volume, 200.0, places=2)
        self.assertAlmostEqual(
            self.product_template.calc_volume, 200.0, places=2
        )

    def test_volume_system_unit_cubic_meters(self):
        """Test that volume is computed in system unit (cubic meters)."""
        self.env['ir.config_parameter'].sudo().set_str(
            'product.volume_in_cubic_feet', '0'
        )
        self.product_template.write({
            'length': 1.0,
            'breadth': 1.0,
            'height': 1.0,
            'length_uom': 'meters',
        })
        self.assertAlmostEqual(self.product_template.volume, 1.0, places=2)
        self.assertEqual(self.product_template.volume_uom, 'cubic_meters')

    def test_volume_system_unit_cubic_feet(self):
        """Test that volume is computed in cubic feet when enabled."""
        self.env['ir.config_parameter'].sudo().set_str(
            'product.volume_in_cubic_feet', '1'
        )
        self.product_template.write({
            'length': 1.0,
            'breadth': 1.0,
            'height': 1.0,
            'length_uom': 'meters',
        })
        self.assertAlmostEqual(self.product_template.volume, 35.3147, places=2)
        self.assertAlmostEqual(
            self.product_template.product_variant_ids.volume, 35.3147, places=2
        )
        # Reset back to default
        self.env['ir.config_parameter'].sudo().set_str(
            'product.volume_in_cubic_feet', '0'
        )

    def test_manual_volume_is_preserved_without_complete_dimensions(self):
        """Incomplete dimensions must not overwrite a manual core volume."""
        product = self.env['product.template'].create({
            'name': 'Manual Volume Product',
            'type': 'consu',
        })
        product.volume = 7.5
        product.write({'length': 2.0, 'breadth': 3.0})

        self.assertAlmostEqual(product.volume, 7.5, places=2)
        self.assertAlmostEqual(
            product.product_variant_ids.volume, 7.5, places=2
        )
        self.assertEqual(product.calc_volume, 0.0)

    def test_clearing_dimensions_clears_calculated_variant_volume(self):
        """Clearing a previously complete dimension set clears stale volume."""
        product = self.env['product.template'].create({
            'name': 'Cleared Dimensions Product',
            'length': 2.0,
            'breadth': 3.0,
            'height': 4.0,
            'length_uom': 'meters',
        })
        product.write({'height': 0.0})

        self.assertEqual(product.product_variant_ids.volume, 0.0)
        self.assertEqual(product.volume, 0.0)
        self.assertEqual(product.calc_volume, 0.0)

    def test_dimension_volume_updates_all_variants(self):
        """Template dimensions should keep all variant volumes consistent."""
        attribute = self.env['product.attribute'].create({
            'name': 'Volume Test Attribute',
            'display_type': 'radio',
            'create_variant': 'always',
            'value_ids': [
                (0, 0, {'name': 'Small'}),
                (0, 0, {'name': 'Large'}),
            ],
        })
        product = self.env['product.template'].create({
            'name': 'Multi Variant Volume Product',
            'type': 'consu',
            'attribute_line_ids': [(0, 0, {
                'attribute_id': attribute.id,
                'value_ids': [(6, 0, attribute.value_ids.ids)],
            })],
            'length': 2.0,
            'breadth': 3.0,
            'height': 4.0,
            'length_uom': 'meters',
        })

        self.assertEqual(len(product.product_variant_ids), 2)
        for variant in product.product_variant_ids:
            self.assertAlmostEqual(variant.volume, 24.0, places=2)
        self.assertAlmostEqual(product.volume, 24.0, places=2)

    def test_volume_unit_parameter_change_resyncs_volume(self):
        """Switching the system volume unit converts stored volumes."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_str('product.volume_in_cubic_feet', '0')
        self.product_template.write({
            'length': 2.0,
            'breadth': 3.0,
            'height': 4.0,
            'length_uom': 'meters',
        })
        self.assertAlmostEqual(self.product_template.volume, 24.0, places=2)

        # Switch the system unit to cubic feet through the settings.
        self.env['res.config.settings'].create({
            'product_volume_volume_in_cubic_feet': '1',
        }).execute()
        expected_feet = 24.0 * 35.3147
        self.assertAlmostEqual(
            self.product_template.volume, expected_feet, places=2
        )
        self.assertAlmostEqual(
            self.product_template.product_variant_ids.volume,
            expected_feet, places=2,
        )
        # The calculated volume in the chosen unit is unaffected.
        self.assertAlmostEqual(
            self.product_template.calc_volume, 24.0, places=2
        )

        # Switch back to cubic meters.
        params.set_str('product.volume_in_cubic_feet', '0')
        self.assertAlmostEqual(self.product_template.volume, 24.0, places=2)


    def test_volume_unit_parameter_delete_resyncs_volume(self):
        """Deleting the cubic feet parameter falls back to cubic meters."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_str('product.volume_in_cubic_feet', '1')
        self.product_template.write({
            'length': 2.0,
            'breadth': 3.0,
            'height': 4.0,
            'length_uom': 'meters',
        })
        self.assertAlmostEqual(
            self.product_template.volume, 24.0 * 35.3147, places=2
        )
        # Deleting an unrelated parameter leaves volumes untouched.
        params.create({'key': 'product_volume.test_key', 'value': 'x'}).unlink()
        self.assertAlmostEqual(
            self.product_template.volume, 24.0 * 35.3147, places=2
        )
        params.search([('key', '=', 'product.volume_in_cubic_feet')]).unlink()
        self.assertAlmostEqual(self.product_template.volume, 24.0, places=2)

    def test_default_volume_uom_follows_system_unit(self):
        """New products default to the system volume unit."""
        params = self.env['ir.config_parameter'].sudo()
        params.set_str('product.volume_in_cubic_feet', '1')
        feet_product = self.env['product.template'].create({
            'name': 'Cubic Feet Default Product',
        })
        self.assertEqual(feet_product.volume_uom, 'cubic_feet')
        params.set_str('product.volume_in_cubic_feet', '0')
        meter_product = self.env['product.template'].create({
            'name': 'Cubic Meter Default Product',
        })
        self.assertEqual(meter_product.volume_uom, 'cubic_meters')

    def test_volume_uom_dynamic_change(self):
        """Test changing volume_uom updates calc_volume."""
        self.product_template.write({
            'length': 150.0,
            'breadth': 10.0,
            'height': 2000.0,
            'length_uom': 'feet',
            'volume_uom': 'cubic_meters',
        })
        expected_m3 = 3000000.0 / 35.3147
        self.assertAlmostEqual(
            self.product_template.volume, expected_m3, places=2
        )
        self.assertAlmostEqual(
            self.product_template.calc_volume, expected_m3, places=2
        )

        # Switch unit to cubic yards
        self.product_template.write({'volume_uom': 'cubic_yards'})
        expected_yards = expected_m3 * 1.308
        self.assertAlmostEqual(
            self.product_template.calc_volume, expected_yards, places=2
        )
        self.assertAlmostEqual(
            self.product_template.volume, expected_m3, places=2
        )

        # Switch unit to cubic feet
        self.product_template.write({'volume_uom': 'cubic_feet'})
        expected_feet = expected_m3 * 35.3147
        self.assertAlmostEqual(
            self.product_template.calc_volume, expected_feet, places=1
        )
        self.assertAlmostEqual(
            self.product_template.volume, expected_m3, places=2
        )

        # Switch unit to cubic inches
        self.product_template.write({'volume_uom': 'cubic_inches'})
        expected_inches = expected_m3 * 61023.7
        self.assertAlmostEqual(
            self.product_template.calc_volume, expected_inches, places=0
        )
        self.assertAlmostEqual(
            self.product_template.volume, expected_m3, places=2
        )
