# -*- coding: utf-8 -*-
from odoo.addons.point_of_sale.tests.test_frontend import TestPointOfSaleHttpCommon
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestPosProductStock(TestPointOfSaleHttpCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.main_pos_config
        cls.pos_config.write({
            'display_stock_setting': True,
            'stock_product': 'on_hand',
            'location_from': 'all_warehouse',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test POS Product',
            'type': 'consu',
            'available_in_pos': True,
            'deny': 5,
        })
        cls.location_1 = cls.env['stock.location'].create({
            'name': 'Test Location 1',
            'usage': 'internal',
        })
        cls.location_2 = cls.env['stock.location'].create({
            'name': 'Test Location 2',
            'usage': 'internal',
        })

    def test_pos_config_onchange_location_from(self):
        """Test the onchange for location_from field in pos.config."""
        self.pos_config.location_from = 'current_warehouse'
        self.pos_config.pos_stock_location_id = self.location_1.id
        self.pos_config._onchange_location_from()
        
        self.pos_config.location_from = 'all_warehouse'
        self.pos_config._onchange_location_from()
        self.assertFalse(self.pos_config.pos_stock_location_id, "Stock location should be False when location_from is all_warehouse")

    def test_res_config_settings_load_pos_data_fields(self):
        """Test fields loaded in res.config.settings for POS."""
        fields = self.env['res.config.settings']._load_pos_data_fields(self.pos_config)
        for field in ['display_stock', 'stock_type', 'stock_from', 'stock_location_id']:
            self.assertIn(field, fields, f"{field} should be loaded for res.config.settings in POS.")

    def test_product_product_load_pos_data_fields(self):
        """Test fields loaded in product.product for POS."""
        pp_fields = self.env['product.product']._load_pos_data_fields(self.pos_config)
        for field in ['qty_available', 'incoming_qty', 'outgoing_qty', 'deny']:
            self.assertIn(field, pp_fields, f"{field} should be loaded for product.product in POS.")

    def test_stock_quant_load_pos_data_fields_and_domain(self):
        """Test fields and domain loaded in stock.quant for POS."""
        fields = self.env['stock.quant']._load_pos_data_fields(self.pos_config)
        for field in ['product_id', 'available_quantity', 'quantity', 'location_id']:
            self.assertIn(field, fields, f"{field} should be loaded for stock.quant in POS.")

        data = {'pos.config': [{'id': self.pos_config.id}]}
        
        # Test domain with all_warehouse
        self.pos_config.write({'location_from': 'all_warehouse'})
        domain_all = self.env['stock.quant']._load_pos_data_domain(data, self.pos_config)
        self.assertTrue(any('location_id' in d and 'in' in d for d in domain_all if isinstance(d, tuple)))

        # Test domain with current_warehouse
        self.pos_config.write({
            'location_from': 'current_warehouse',
            'pos_stock_location_id': self.location_1.id,
        })
        domain_current = self.env['stock.quant']._load_pos_data_domain(data, self.pos_config)
        self.assertIn(('location_id', '=', self.location_1.id), domain_current)

    def test_pos_session_load_pos_data_models(self):
        """Test models loaded in pos.session for POS."""
        models = self.env['pos.session']._load_pos_data_models(self.pos_config)
        for model in ['res.config.settings', 'stock.quant', 'stock.move.line', 'ir.config_parameter']:
            self.assertIn(model, models, f"{model} should be loaded for pos.session in POS.")

    def test_stock_move_line_load_pos_data_fields(self):
        """Test fields loaded in stock.move.line for POS."""
        fields = self.env['stock.move.line']._load_pos_data_fields(self.pos_config)
        for field in ['product_id', 'location_dest_id', 'quantity', 'location_id']:
            self.assertIn(field, fields, f"{field} should be loaded for stock.move.line in POS.")

    def test_ir_config_parameter_load_pos_data_fields(self):
        """Test fields loaded in ir.config_parameter for POS."""
        fields = self.env['ir.config_parameter']._load_pos_data_fields(self.pos_config)
        for field in ['key', 'value']:
            self.assertIn(field, fields, f"{field} should be loaded for ir.config_parameter in POS.")
