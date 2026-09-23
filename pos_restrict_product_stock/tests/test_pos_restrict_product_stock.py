# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestPosRestrictProductStock(TransactionCase):
    """Test the location-specific stock data loaded by the POS."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env['stock.warehouse'].search([
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        cls.source_location = cls.warehouse.lot_stock_id
        cls.child_location = cls.env['stock.location'].create({
            'name': 'POS Test Child Location',
            'location_id': cls.source_location.id,
            'usage': 'internal',
            'company_id': cls.env.company.id,
        })
        cls.other_location = cls.env['stock.location'].create({
            'name': 'POS Test Other Location',
            'location_id': cls.source_location.location_id.id,
            'usage': 'internal',
            'company_id': cls.env.company.id,
        })
        cls.env['account.journal'].create({
            'name': 'POS Stock Test Bank',
            'code': 'PSTB',
            'type': 'bank',
            'company_id': cls.env.company.id,
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'POS Stock Restriction Test',
            'picking_type_id': cls.warehouse.out_type_id.id,
        })

    def _create_product(self, name):
        return self.env['product.product'].create({
            'name': name,
            'is_storable': True,
            'available_in_pos': True,
        })

    def _set_quantity(self, product, location, quantity):
        self.env['stock.quant']._update_available_quantity(
            product, location, quantity,
        )

    def test_pos_config_stock_options_are_available_in_settings(self):
        self.assertEqual(self.pos_config.stock_type, 'qty_on_hand')
        self.assertFalse(self.pos_config.is_display_stock)
        self.assertFalse(self.pos_config.is_restrict_product)

        settings = self.env['res.config.settings'].with_context(
            default_pos_config_id=self.pos_config.id,
        ).create({
            'is_display_stock': True,
            'is_restrict_product': True,
            'stock_type': 'both',
        })
        settings.execute()

        self.assertTrue(self.pos_config.is_display_stock)
        self.assertTrue(self.pos_config.is_restrict_product)
        self.assertEqual(self.pos_config.stock_type, 'both')

    def test_pos_data_fields_include_stock_quantities(self):
        product_fields = self.env['product.product']._load_pos_data_fields(
            self.pos_config,
        )
        template_fields = self.env['product.template']._load_pos_data_fields(
            self.pos_config,
        )

        self.assertEqual(product_fields.count('qty_available'), 1)
        self.assertEqual(product_fields.count('virtual_available'), 1)
        self.assertIn('type', product_fields)
        self.assertEqual(template_fields.count('qty_available'), 1)
        self.assertEqual(template_fields.count('virtual_available'), 1)

    def test_product_stock_is_limited_to_pos_source_location(self):
        stocked_product = self._create_product('POS Stocked Product')
        out_of_scope_product = self._create_product('POS Out Of Scope Product')
        self._set_quantity(stocked_product, self.source_location, 4)
        self._set_quantity(stocked_product, self.child_location, 6)
        self._set_quantity(stocked_product, self.other_location, 20)
        self._set_quantity(out_of_scope_product, self.other_location, 8)

        loaded_products = self.env['product.product']._load_pos_data_read(
            stocked_product | out_of_scope_product, self.pos_config,
        )
        quantities = {
            product['id']: (product['qty_available'], product['virtual_available'])
            for product in loaded_products
        }

        self.assertEqual(quantities[stocked_product.id], (10, 10))
        self.assertEqual(quantities[out_of_scope_product.id], (0, 0))

    def test_template_stock_is_limited_to_pos_source_location(self):
        stocked_product = self._create_product('POS Template Stocked Product')
        out_of_scope_product = self._create_product('POS Template Out Of Scope Product')
        self._set_quantity(stocked_product, self.child_location, 7)
        self._set_quantity(stocked_product, self.other_location, 20)
        self._set_quantity(out_of_scope_product, self.other_location, 3)

        loaded_templates = self.env['product.template']._load_pos_data_read(
            stocked_product.product_tmpl_id | out_of_scope_product.product_tmpl_id,
            self.pos_config,
        )
        quantities = {
            template['id']: (template['qty_available'], template['virtual_available'])
            for template in loaded_templates
        }

        self.assertEqual(quantities[stocked_product.product_tmpl_id.id], (7, 7))
        self.assertEqual(
            quantities[out_of_scope_product.product_tmpl_id.id], (0, 0),
        )
