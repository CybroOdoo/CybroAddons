# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from unittest.mock import patch
from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLowStocksProductAlert(TransactionCase):
    """Test suite covering Python model logic in low_stocks_product_alert."""

    def setUp(self):
        super().setUp()
        self.stock_location = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [self.env.company.id, False]),
        ], limit=1)
        if not self.stock_location:
            self.stock_location = self.env['stock.location'].create({
                'name': 'Test Low Stock Location',
                'usage': 'internal',
                'company_id': self.env.company.id,
            })

        # Fresh storable product for each test
        self.storable_tmpl = self.env['product.template'].create({
            'name': 'Low Stock Test Product',
            'type': 'consu',
            'is_storable': True,
            'available_in_pos': True,
        })
        self.storable_product = self.storable_tmpl.product_variant_id

        # Fresh service / non-storable product for each test
        self.service_tmpl = self.env['product.template'].create({
            'name': 'Low Stock Test Service',
            'type': 'service',
            'available_in_pos': True,
        })
        self.service_product = self.service_tmpl.product_variant_id

        # POS Config
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test Low Stock POS Config',
        })

    def _set_config_parameters(self, is_alert, min_alert):
        """Helper to set ir.config_parameter values directly."""
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_str('low_stocks_product_alert.is_low_stock_alert', 'True' if is_alert else 'False')
        ir_config.set_str('low_stocks_product_alert.min_low_stock_alert', str(min_alert))

    def _set_stock_qty(self, product, qty):
        """Helper to accurately set on-hand stock and invalidate cache."""
        product.invalidate_recordset(['qty_available'])
        product.product_tmpl_id.invalidate_recordset(['qty_available'])
        current = product.qty_available
        diff = qty - current
        if diff != 0:
            self.env['stock.quant']._update_available_quantity(product, self.stock_location, diff)
            product.invalidate_recordset(['qty_available'])
            product.product_tmpl_id.invalidate_recordset(['qty_available'])

    def test_01_res_config_settings(self):
        """Test configuration settings read and write behavior."""
        settings = self.env['res.config.settings'].create({
            'is_low_stock_alert': True,
            'min_low_stock_alert': 15,
        })
        settings.execute()

        ir_config = self.env['ir.config_parameter'].sudo()
        self.assertEqual(ir_config.get_str('low_stocks_product_alert.is_low_stock_alert'), 'True')
        self.assertEqual(ir_config.get_str('low_stocks_product_alert.min_low_stock_alert'), '15')

        # Test new settings instance retrieves the saved values
        new_settings = self.env['res.config.settings'].create({})
        self.assertTrue(new_settings.is_low_stock_alert)
        self.assertEqual(new_settings.min_low_stock_alert, 15)

    def test_02_alert_disabled(self):
        """When low stock alert is disabled, alert fields must remain False."""
        self._set_config_parameters(is_alert=False, min_alert=10)

        self.storable_product._compute_alert_state()
        self.storable_tmpl._compute_alert_state()

        self.assertFalse(self.storable_product.alert_state)
        self.assertFalse(self.storable_product.alert_tag)

        self.assertFalse(self.storable_tmpl.alert_state)
        self.assertFalse(self.storable_tmpl.alert_tag)

    def test_03_storable_product_low_stock_alert(self):
        """When stock is below the limit, alert_state is True and alert_tag is computed."""
        self._set_config_parameters(is_alert=True, min_alert=10)
        self._set_stock_qty(self.storable_product, 5.0)
        self.assertEqual(self.storable_product.qty_available, 5.0)

        self.storable_product._compute_alert_state()
        self.storable_tmpl._compute_alert_state()

        self.assertTrue(self.storable_product.alert_state)
        self.assertEqual(self.storable_product.alert_tag, '5')

        self.assertTrue(self.storable_tmpl.alert_state)
        self.assertEqual(self.storable_tmpl.alert_tag, '5')

    def test_04_storable_product_exact_threshold(self):
        """When stock equals the limit exactly, alert_state is triggered."""
        self._set_config_parameters(is_alert=True, min_alert=10)
        self._set_stock_qty(self.storable_product, 10.0)
        self.assertEqual(self.storable_product.qty_available, 10.0)

        self.storable_product._compute_alert_state()
        self.assertTrue(self.storable_product.alert_state)
        self.assertEqual(self.storable_product.alert_tag, '10')

    def test_05_storable_product_fractional_qty(self):
        """When stock is fractional, alert_tag preserves the decimal representation."""
        self._set_config_parameters(is_alert=True, min_alert=10)
        self._set_stock_qty(self.storable_product, 4.5)
        self.assertEqual(self.storable_product.qty_available, 4.5)

        self.storable_product._compute_alert_state()
        self.assertTrue(self.storable_product.alert_state)
        self.assertEqual(self.storable_product.alert_tag, '4.5')

    def test_06_storable_product_above_threshold(self):
        """When stock is strictly above the limit, alert_state and alert_tag are False."""
        self._set_config_parameters(is_alert=True, min_alert=10)
        self._set_stock_qty(self.storable_product, 25.0)
        self.assertEqual(self.storable_product.qty_available, 25.0)

        self.storable_product._compute_alert_state()
        self.storable_tmpl._compute_alert_state()

        self.assertFalse(self.storable_product.alert_state)
        self.assertFalse(self.storable_product.alert_tag)

        self.assertFalse(self.storable_tmpl.alert_state)
        self.assertFalse(self.storable_tmpl.alert_tag)

    def test_07_service_product_never_triggers_alert(self):
        """Service products (is_storable = False) should never trigger low stock alert."""
        self._set_config_parameters(is_alert=True, min_alert=10)

        self.service_product._compute_alert_state()
        self.service_tmpl._compute_alert_state()

        self.assertFalse(self.service_product.alert_state)
        self.assertFalse(self.service_product.alert_tag)

        self.assertFalse(self.service_tmpl.alert_state)
        self.assertFalse(self.service_tmpl.alert_tag)

    def test_08_load_pos_data_fields(self):
        """Verify low stock fields are registered for POS data loading."""
        prod_fields = self.env['product.product']._load_pos_data_fields(self.pos_config)
        for field in ['alert_tag', 'alert_state']:
            self.assertIn(field, prod_fields, f"'{field}' must be included in product.product pos fields.")

        tmpl_fields = self.env['product.template']._load_pos_data_fields(self.pos_config)
        for field in ['alert_tag', 'alert_state']:
            self.assertIn(field, tmpl_fields, f"'{field}' must be included in product.template pos fields.")

    def test_09_invalid_threshold(self):
        """When min_low_stock_alert is non-numeric, fallback limit is 0.0."""
        self._set_stock_qty(self.storable_product, 5.0)
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_str('low_stocks_product_alert.is_low_stock_alert', 'True')
        ir_config.set_str('low_stocks_product_alert.min_low_stock_alert', 'invalid_limit')

        self.storable_product._compute_alert_state()
        self.storable_tmpl._compute_alert_state()

        # Since qty 5.0 is greater than fallback limit 0.0, alert_state must be False
        self.assertFalse(self.storable_tmpl.alert_state)
        self.assertFalse(self.storable_tmpl.alert_tag)

    def test_10_load_pos_data_fields_branches(self):
        """Test set branch in _load_pos_data_fields across models and mixin."""
        import odoo.addons.point_of_sale.models.product_template as pt_mod
        import odoo.addons.point_of_sale.models.product_product as pp_mod

        with patch.object(pt_mod.ProductTemplate, '_load_pos_data_fields', return_value={'id', 'name'}):
            fields = self.env['product.template']._load_pos_data_fields(self.pos_config)
            self.assertIn('alert_tag', fields)
            self.assertIn('alert_state', fields)

        with patch.object(pp_mod.ProductProduct, '_load_pos_data_fields', return_value={'id', 'lst_price'}):
            fields = self.env['product.product']._load_pos_data_fields(self.pos_config)
            self.assertIn('alert_tag', fields)
            self.assertIn('alert_state', fields)

        # Mixin methods directly
        res_list = self.env['product.low.stock.alert.mixin']._load_pos_data_fields(self.pos_config)
        self.assertIn('alert_tag', res_list)
        self.assertIn('alert_state', res_list)


@tagged('post_install', '-at_install')
class TestLowStocksProductAlertTour(HttpCase):
    """Tour tests for low stocks product alert in the Point of Sale UI."""

    def test_pos_low_stocks_tour(self):
        """Launch POS tour and ensure low stock product card renders without errors."""
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_str('low_stocks_product_alert.is_low_stock_alert', 'True')
        ir_config.set_str('low_stocks_product_alert.min_low_stock_alert', '10')

        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            pos_config = self.env['pos.config'].create({'name': 'Low Stock Tour POS Config'})

        self.start_tour(f"/pos/ui/{pos_config.id}", 'pos_low_stocks_alert_tour', login='admin')
