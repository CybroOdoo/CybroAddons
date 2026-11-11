# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPosCustomPercentageTipFixed(TransactionCase):
    """Test suite for POS Custom Percentage Tip functionality."""

    def setUp(self):
        super().setUp()
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Shop',
        })
        tip_product = self.env['product.product'].search(
            [('available_in_pos', '=', True)],
            limit=1,
        )
        if not tip_product:
            tip_product = self.env['product.product'].create({
                'name': 'Tip Product',
                'type': 'service',
                'available_in_pos': True,
                'list_price': 0.0,
            })
        self.pos_config.write({
            'iface_tipproduct': True,
            'tip_product_id': tip_product.id,
        })
        self.test_product = self.env['product.product'].search(
            [('available_in_pos', '=', True), ('id', '!=', tip_product.id)],
            limit=1,
        )
        if not self.test_product:
            self.test_product = self.env['product.product'].create({
                'name': 'Test Coffee',
                'type': 'consu',
                'available_in_pos': True,
                'list_price': 50.0,
            })

    def test_custom_tip_percentage_field_exists(self):
        """Verify custom_tip_percentage exists on pos.config."""
        self.assertIn(
            'custom_tip_percentage',
            self.env['pos.config']._fields,
            "Field 'custom_tip_percentage' must exist on pos.config",
        )

    def test_custom_tip_percentage_default_is_zero(self):
        """Verify default custom tip percentage is 0.0."""
        new_config = self.env['pos.config'].create({
            'name': 'Default Tip POS',
        })
        self.assertEqual(
            new_config.custom_tip_percentage,
            0.0,
            "Default value of 'custom_tip_percentage' should be 0.0",
        )

    def test_set_custom_tip_percentage(self):
        """Verify setting custom tip percentage on pos.config."""
        self.pos_config.write({'custom_tip_percentage': 15.0})
        self.assertEqual(
            self.pos_config.custom_tip_percentage,
            15.0,
            "Custom tip percentage should be stored as 15.0",
        )

    def test_update_custom_tip_percentage(self):
        """Verify updating custom tip percentage on pos.config."""
        self.pos_config.write({'custom_tip_percentage': 10.0})
        self.pos_config.write({'custom_tip_percentage': 20.0})
        self.assertEqual(
            self.pos_config.custom_tip_percentage,
            20.0,
            "Custom tip percentage should be updated to 20.0",
        )

    def test_res_config_settings_related_field(self):
        """Verify settings related field exists and is editable."""
        field = self.env['res.config.settings']._fields.get(
            'pos_custom_tip_percentage',
        )
        self.assertIsNotNone(
            field,
            "Field 'pos_custom_tip_percentage' not found on settings",
        )
        self.assertEqual(
            field.type,
            'float',
            "Field 'pos_custom_tip_percentage' should be of type Float",
        )
        self.assertFalse(
            field.readonly,
            "Field 'pos_custom_tip_percentage' must have readonly=False",
        )

    def test_res_config_settings_save_and_persist(self):
        """Test setting percentage via res.config.settings persists."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'pos_custom_tip_percentage': 18.5,
        })
        settings.execute()
        self.assertAlmostEqual(
            self.pos_config.custom_tip_percentage,
            18.5,
            places=2,
            msg="Executing settings must persist percentage to pos.config",
        )

    def test_res_config_reflects_pos_config_tip_percentage(self):
        """Verify settings related field reflects pos.config value."""
        self.pos_config.write({'custom_tip_percentage': 12.5})
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })
        self.assertAlmostEqual(
            settings.pos_custom_tip_percentage,
            12.5,
            places=2,
            msg="Settings related field must reflect the pos.config value",
        )

    def test_custom_tip_percentage_negative_constraint(self):
        """Verify negative tip percentage raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.pos_config.write({'custom_tip_percentage': -5.0})

    def test_custom_tip_percentage_over_hundred_constraint(self):
        """Verify tip percentage > 100 raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.pos_config.write({'custom_tip_percentage': 105.0})

    def test_custom_tip_percentage_boundary_values(self):
        """Verify boundary percentages 0.0 and 100.0 are accepted."""
        self.pos_config.write({'custom_tip_percentage': 0.0})
        self.assertEqual(self.pos_config.custom_tip_percentage, 0.0)
        self.pos_config.write({'custom_tip_percentage': 100.0})
        self.assertEqual(self.pos_config.custom_tip_percentage, 100.0)

    def test_iface_tipproduct_enabled(self):
        """Verify tip product interface is active on config."""
        self.assertTrue(
            self.pos_config.iface_tipproduct,
            "Tip product feature should be enabled on the POS config",
        )

    def test_tip_product_assigned(self):
        """Verify tip product is correctly linked to POS config."""
        self.assertTrue(
            self.pos_config.tip_product_id,
            "A tip product should be assigned to the POS configuration",
        )

    def test_multiple_pos_configs_independent_tip_percentages(self):
        """Verify different POS configs maintain independent tips."""
        config_a = self.env['pos.config'].create({
            'name': 'POS Config A',
            'custom_tip_percentage': 5.0,
        })
        config_b = self.env['pos.config'].create({
            'name': 'POS Config B',
            'custom_tip_percentage': 18.0,
        })
        self.assertNotEqual(
            config_a.custom_tip_percentage,
            config_b.custom_tip_percentage,
            "Different POS configs must store independent tip percentages",
        )
        self.assertEqual(config_a.custom_tip_percentage, 5.0)
        self.assertEqual(config_b.custom_tip_percentage, 18.0)

    def test_pos_order_tip_computation_and_line_creation(self):
        """Test calculating tip and adding tip line to POS order."""
        self.pos_config.write({'custom_tip_percentage': 10.0})
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })
        pos_order = self.env['pos.order'].create({
            'session_id': session.id,
            'lines': [(0, 0, {
                'product_id': self.test_product.id,
                'qty': 2,
                'price_unit': 50.0,
                'price_subtotal': 100.0,
                'price_subtotal_incl': 100.0,
            })],
            'amount_tax': 0.0,
            'amount_total': 100.0,
            'amount_paid': 0.0,
            'amount_return': 0.0,
        })
        base_total = pos_order.amount_total
        tip_percent = self.pos_config.custom_tip_percentage / 100.0
        tip_amount = base_total * tip_percent
        self.assertAlmostEqual(tip_amount, 10.0, places=2)

        # Apply the tip orderline using the configured tip product
        pos_order.write({
            'lines': [(0, 0, {
                'product_id': self.pos_config.tip_product_id.id,
                'qty': 1,
                'price_unit': tip_amount,
                'price_subtotal': tip_amount,
                'price_subtotal_incl': tip_amount,
            })],
            'amount_total': base_total + tip_amount,
        })
        self.assertAlmostEqual(pos_order.amount_total, 110.0, places=2)
        tip_lines = pos_order.lines.filtered(
            lambda line: line.product_id == self.pos_config.tip_product_id,
        )
        self.assertEqual(len(tip_lines), 1)
        self.assertAlmostEqual(tip_lines.price_unit, 10.0, places=2)

    def test_pos_order_zero_percentage_no_tip(self):
        """Test zero tip percentage results in zero tip amount."""
        self.pos_config.write({'custom_tip_percentage': 0.0})
        base_total = 150.0
        tip_percent = self.pos_config.custom_tip_percentage / 100.0
        tip_amount = base_total * tip_percent
        self.assertEqual(tip_amount, 0.0)
