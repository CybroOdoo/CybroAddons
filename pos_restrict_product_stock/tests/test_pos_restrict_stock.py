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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosRestrictStock(TransactionCase):
    """Test suite for POS stock display and restriction module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.stock_location = cls.env.ref(
            'stock.stock_location_stock', raise_if_not_found=False
        )
        if not cls.stock_location:
            cls.stock_location = cls.env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('company_id', 'in', [cls.company.id, False]),
            ], limit=1)

        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Shop',
            'is_display_stock': True,
            'is_restrict_product': True,
            'stock_type': 'both',
        })

        cls.storable_product = cls.env['product.product'].create({
            'name': 'Storable Test Product',
            'is_storable': True,
            'type': 'consu',
            'available_in_pos': True,
        })

        cls.consumable_product = cls.env['product.product'].create({
            'name': 'Consumable Test Product',
            'is_storable': False,
            'type': 'consu',
            'available_in_pos': True,
        })

    def test_01_pos_config_stock_fields(self):
        """Test stock display and restriction configurations on pos.config."""
        self.assertTrue(self.pos_config.is_display_stock)
        self.assertTrue(self.pos_config.is_restrict_product)
        self.assertEqual(self.pos_config.stock_type, 'both')

        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'is_display_stock': False,
            'is_restrict_product': True,
            'stock_type': 'qty_on_hand',
        })
        settings.execute()
        self.assertFalse(self.pos_config.is_display_stock)
        self.assertTrue(self.pos_config.is_restrict_product)
        self.assertEqual(self.pos_config.stock_type, 'qty_on_hand')

    def test_02_load_pos_data_fields(self):
        """Test stock and storable fields are added to POS loaded fields."""
        prod_fields = self.env['product.product']._load_pos_data_fields(
            self.pos_config
        )
        self.assertIn('qty_available', prod_fields)
        self.assertIn('virtual_available', prod_fields)
        self.assertIn('is_storable', prod_fields)

        tmpl_fields = self.env['product.template']._load_pos_data_fields(
            self.pos_config.id
        )
        self.assertIn('qty_available', tmpl_fields)
        self.assertIn('virtual_available', tmpl_fields)
        self.assertIn('is_storable', tmpl_fields)

    def test_03_load_pos_data_read_location_stock(self):
        """Test stock quantities are properly scoped to POS location."""
        if self.stock_location:
            self.env['stock.quant']._update_available_quantity(
                self.storable_product, self.stock_location, 25.0
            )

        products = self.storable_product | self.consumable_product
        read_res = self.env['product.product']._load_pos_data_read(
            products, self.pos_config
        )
        res_by_id = {d['id']: d for d in read_res if 'id' in d}

        storable_dict = res_by_id.get(self.storable_product.id)
        self.assertIsNotNone(storable_dict)
        picking_type = getattr(self.pos_config, 'picking_type_id', False)
        src_loc = (
            picking_type.default_location_src_id if picking_type else None
        )
        if self.stock_location and src_loc == self.stock_location:
            self.assertEqual(storable_dict.get('qty_available'), 25.0)

        consumable_dict = res_by_id.get(self.consumable_product.id)
        self.assertIsNotNone(consumable_dict)
        self.assertFalse(consumable_dict.get('is_storable'))
