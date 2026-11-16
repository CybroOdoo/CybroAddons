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
from unittest.mock import MagicMock, patch
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.product_nutrition_allergen.controllers.main import WebsiteSaleController


@tagged('post_install', '-at_install')
class TestProductNutritionController(TransactionCase):
    """Test suite for WebsiteSaleController routes and helper methods."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = WebsiteSaleController()

        cls.uom_g = cls.env.ref('uom.product_uom_gram', raise_if_not_found=False)
        if not cls.uom_g:
            cls.uom_g = cls.env['uom.uom'].search([('name', '=', 'g')], limit=1)
        if not cls.uom_g:
            uom_unit_categ = cls.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
            if not uom_unit_categ:
                uom_unit_categ = cls.env['uom.category'].create({'name': 'Weight'})
            cls.uom_g = cls.env['uom.uom'].create({
                'name': 'g',
                'category_id': uom_unit_categ.id,
                'uom_type': 'reference',
            })

        cls.product = cls.env['product.template'].create({
            'name': 'Fresh Fruit Smoothie',
            'nutrition_details': True,
            'ingredients_details': True,
            'allergy_details': True,
            'nutrition_amount': 250.0,
            'unit_id': cls.uom_g.id,
            'ingredients_information': 'Banana, Strawberry, Apple juice.',
            'allergy_information': 'No common allergens.',
            'nutrition_ids': [
                (0, 0, {
                    'name': 'Vitamin C',
                    'nutrition_value': 45.0,
                    'uom_id': cls.uom_g.id,
                }),
            ],
        })

    def test_parse_product_id(self):
        """Test URL parsing helper for product ids."""
        parse = self.controller._parse_product_id

        self.assertEqual(parse(f'fresh-fruit-smoothie-{self.product.id}'), self.product.id)
        self.assertEqual(parse(f'product-{self.product.id}#nutrition'), self.product.id)
        self.assertEqual(parse(f'product-{self.product.id}?variant=1'), self.product.id)
        self.assertEqual(parse(f'shop-product-{self.product.id}/'), self.product.id)
        self.assertEqual(parse(str(self.product.id)), self.product.id)

        self.assertIsNone(parse(''))
        self.assertIsNone(parse(None))
        self.assertIsNone(parse('invalid-slug-without-id'))
        self.assertIsNone(parse(f'shop/product/{self.product.id}/'))

    def test_product_ingredients_details_route(self):
        """Test fetching ingredient information for valid and invalid products."""
        mock_request = MagicMock()
        mock_request.env = self.env

        with patch('odoo.addons.product_nutrition_allergen.controllers.main.request', mock_request):
            result = self.controller.product_ingredients_details(f'fresh-fruit-smoothie-{self.product.id}')
            self.assertEqual(result, 'Banana, Strawberry, Apple juice.')

            invalid_result = self.controller.product_ingredients_details('non-existent-9999999')
            self.assertEqual(invalid_result, '')

            empty_result = self.controller.product_ingredients_details('')
            self.assertEqual(empty_result, '')

    def test_product_allergy_details_route(self):
        """Test fetching allergy information for valid and invalid products."""
        mock_request = MagicMock()
        mock_request.env = self.env

        with patch('odoo.addons.product_nutrition_allergen.controllers.main.request', mock_request):
            result = self.controller.product_allergy_details(f'fresh-fruit-smoothie-{self.product.id}')
            self.assertEqual(result, 'No common allergens.')

            invalid_result = self.controller.product_allergy_details('non-existent-9999999')
            self.assertEqual(invalid_result, '')

            empty_result = self.controller.product_allergy_details('')
            self.assertEqual(empty_result, '')

    def test_product_nutrition_details_route(self):
        """Test fetching nutrition details list for a product."""
        mock_request = MagicMock()
        mock_request.env = self.env
        mock_request.uid = self.env.uid

        with patch('odoo.addons.product_nutrition_allergen.controllers.main.request', mock_request):
            result = self.controller.product_nutrition_details(f'fresh-fruit-smoothie-{self.product.id}')
            self.assertIsInstance(result, list)
            if result:
                self.assertEqual(result[0]['name'], 'Vitamin C')
                self.assertEqual(result[0]['nutrition_value'], 45.0)

            invalid_result = self.controller.product_nutrition_details('non-existent-9999999')
            self.assertEqual(invalid_result, [])

