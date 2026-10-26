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
class TestProductTemplate(TransactionCase):
    """Test suite for product.template extension (product_template.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand_apple = cls.env['mobile.brand'].create({'brand_name': 'Apple Inc'})
        cls.brand_google = cls.env['mobile.brand'].create({'brand_name': 'Google Inc'})

        cls.model_iphone = cls.env['brand.model'].create({
            'mobile_brand_name': cls.brand_apple.id,
            'mobile_brand_models': 'iPhone 16 Pro',
        })
        cls.model_pixel = cls.env['brand.model'].create({
            'mobile_brand_name': cls.brand_google.id,
            'mobile_brand_models': 'Pixel 9 Pro',
        })

    def test_01_parts_fields_persistence(self):
        """Test mobile parts custom fields on product.template."""
        template = self.env['product.template'].create({
            'name': 'AMOLED Screen Display',
            'is_a_parts': True,
            'model_colour': 'Space Black',
            'extra_descriptions': 'Replacement AMOLED panel with frame',
            'list_price': 160.0,
        })
        self.assertTrue(template.is_a_parts)
        self.assertEqual(template.model_colour, 'Space Black')
        self.assertEqual(template.extra_descriptions, 'Replacement AMOLED panel with frame')

    def test_02_allowed_model_ids_computation(self):
        """Test allowed_model_ids computation with and without brand_name."""
        template = self.env['product.template'].create({
            'name': 'Universal Battery',
            'is_a_parts': True,
        })
        # Without brand_name, should include all models
        self.assertIn(self.model_iphone.id, template.allowed_model_ids.ids)
        self.assertIn(self.model_pixel.id, template.allowed_model_ids.ids)

        # Set brand to Apple
        template.brand_name = self.brand_apple.id
        self.assertIn(self.model_iphone.id, template.allowed_model_ids.ids)
        self.assertNotIn(self.model_pixel.id, template.allowed_model_ids.ids)

        # Change brand to Google
        template.brand_name = self.brand_google.id
        self.assertNotIn(self.model_iphone.id, template.allowed_model_ids.ids)
        self.assertIn(self.model_pixel.id, template.allowed_model_ids.ids)
