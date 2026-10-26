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
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosCrossSelling(TransactionCase):
    """Test suite for pos.cross.selling model functionality, constraints,
    and cross-selling products retrieval.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Create products available in POS
        cls.product_main_1 = cls.env['product.product'].create({
            'name': 'Burger Combo Main',
            'available_in_pos': True,
            'lst_price': 120.0,
        })
        cls.product_main_2 = cls.env['product.product'].create({
            'name': 'Pizza Combo Main',
            'available_in_pos': True,
            'lst_price': 250.0,
        })
        cls.product_cross_1 = cls.env['product.product'].create({
            'name': 'French Fries',
            'available_in_pos': True,
            'lst_price': 40.0,
        })
        cls.product_cross_2 = cls.env['product.product'].create({
            'name': 'Soft Drink',
            'available_in_pos': True,
            'lst_price': 25.0,
        })
        cls.product_cross_3 = cls.env['product.product'].create({
            'name': 'Ice Cream',
            'available_in_pos': True,
            'lst_price': 35.0,
        })
        cls.product_not_in_pos = cls.env['product.product'].create({
            'name': 'Unconfigured Product',
            'available_in_pos': True,
            'lst_price': 10.0,
        })

        # Create standard cross selling configuration for product_main_1
        cls.cross_selling = cls.env['pos.cross.selling'].create({
            'product_id': cls.product_main_1.id,
            'active': True,
            'pos_cross_product_ids': [
                (0, 0, {'product_id': cls.product_cross_1.id, 'active': True}),
                (0, 0, {'product_id': cls.product_cross_2.id, 'active': True}),
            ],
        })

    def test_01_create_cross_selling_record(self):
        """Test successful creation and field population of pos.cross.selling."""
        self.assertTrue(self.cross_selling.id, "pos.cross.selling record should be created.")
        self.assertEqual(
            self.cross_selling.product_id,
            self.product_main_1,
            "Product ID should match configured product."
        )
        self.assertTrue(self.cross_selling.active, "active should default to True.")
        self.assertEqual(
            len(self.cross_selling.pos_cross_product_ids),
            2,
            "Cross selling should have exactly 2 product lines."
        )

    def test_02_rec_name_and_display_name(self):
        """Test that _rec_name returns product_id display name."""
        self.assertEqual(
            self.cross_selling.display_name,
            self.product_main_1.display_name,
            "Display name should match the configured product's display name."
        )

    def test_03_write_and_add_lines(self):
        """Test updating fields and adding a new cross-selling line."""
        self.cross_selling.write({
            'pos_cross_product_ids': [
                (0, 0, {'product_id': self.product_cross_3.id, 'active': True}),
            ],
        })
        self.assertEqual(
            len(self.cross_selling.pos_cross_product_ids),
            3,
            "Cross selling record should now have 3 product lines."
        )
        self.assertIn(
            self.product_cross_3,
            self.cross_selling.pos_cross_product_ids.mapped('product_id'),
            "Newly added product should be in pos_cross_product_ids."
        )

    def test_04_unlink_cross_selling(self):
        """Test unlinking a pos.cross.selling record clears parent relation on lines."""
        temp_cross = self.env['pos.cross.selling'].create({
            'product_id': self.product_main_2.id,
            'pos_cross_product_ids': [
                (0, 0, {'product_id': self.product_cross_3.id}),
            ],
        })
        temp_line = temp_cross.pos_cross_product_ids
        self.assertTrue(temp_cross.exists(), "Temporary record should exist before unlink.")

        temp_cross.unlink()
        self.assertFalse(temp_cross.exists(), "Record should not exist after unlink.")
        self.assertFalse(
            temp_line.pos_cross_product_id,
            "Associated cross-selling line pos_cross_product_id should be cleared."
        )

    def test_05_archive_and_unarchive(self):
        """Test archiving and unarchiving pos.cross.selling record."""
        self.cross_selling.active = False
        self.assertFalse(self.cross_selling.active, "Record should be archived.")

        # Default search shouldn't include archived record
        found = self.env['pos.cross.selling'].search([('id', '=', self.cross_selling.id)])
        self.assertFalse(found, "Archived record should not appear in default active search.")

        # Search with active_test=False should include it
        found_archived = self.env['pos.cross.selling'].with_context(active_test=False).search(
            [('id', '=', self.cross_selling.id)]
        )
        self.assertTrue(found_archived, "Archived record should appear when active_test is False.")

        # Restore active state
        self.cross_selling.active = True
        self.assertTrue(self.cross_selling.active, "Record should be restored to active.")

    def test_06_constraint_duplicate_product_id_on_create(self):
        """Test that creating a second pos.cross.selling record with the same product_id raises ValidationError."""
        expected_msg = f"A cross-selling product already exists for the product {self.product_main_1.name}."
        with self.assertRaises(ValidationError) as error_context:
            self.env['pos.cross.selling'].create({
                'product_id': self.product_main_1.id,
                'pos_cross_product_ids': [
                    (0, 0, {'product_id': self.product_cross_3.id}),
                ],
            })
        self.assertIn(expected_msg, str(error_context.exception))

    def test_07_constraint_duplicate_product_id_on_write(self):
        """Test that updating product_id to an already configured product raises ValidationError."""
        record_2 = self.env['pos.cross.selling'].create({
            'product_id': self.product_main_2.id,
            'pos_cross_product_ids': [
                (0, 0, {'product_id': self.product_cross_1.id}),
            ],
        })
        expected_msg = f"A cross-selling product already exists for the product {self.product_main_1.name}."
        with self.assertRaises(ValidationError) as error_context:
            record_2.write({'product_id': self.product_main_1.id})
        self.assertIn(expected_msg, str(error_context.exception))

    def test_08_constraint_distinct_products_allowed(self):
        """Test that multiple pos.cross.selling records with distinct product_ids can be created."""
        record_2 = self.env['pos.cross.selling'].create({
            'product_id': self.product_main_2.id,
            'pos_cross_product_ids': [
                (0, 0, {'product_id': self.product_cross_3.id}),
            ],
        })
        self.assertTrue(record_2.id, "Second cross-selling record with distinct product should succeed.")

    def test_09_check_pos_cross_product_ids_constraint(self):
        """Test that _check_pos_cross_product_ids executes cleanly on records."""
        # Execution of constraint should not raise an exception
        self.cross_selling._check_pos_cross_product_ids()

    def test_10_get_cross_selling_products_no_configuration(self):
        """Test get_cross_selling_products returns empty list when product has no cross selling configured."""
        result = self.env['pos.cross.selling'].get_cross_selling_products(self.product_not_in_pos.id)
        self.assertEqual(result, [], "Should return empty list for product with no cross selling.")

    def test_11_get_cross_selling_products_success(self):
        """Test get_cross_selling_products returns list of configured cross products."""
        result = self.env['pos.cross.selling'].get_cross_selling_products(self.product_main_1.id)
        self.assertEqual(len(result), 2, "Should return 2 cross-selling products.")
        result_ids = [item['id'] for item in result]
        self.assertIn(self.product_cross_1.id, result_ids)
        self.assertIn(self.product_cross_2.id, result_ids)

    def test_12_get_cross_selling_products_item_structure_and_values(self):
        """Test get_cross_selling_products items have correct keys, values, and image URLs."""
        result = self.env['pos.cross.selling'].get_cross_selling_products(self.product_main_1.id)
        for item in result:
            self.assertIn('id', item)
            self.assertIn('image', item)
            self.assertIn('name', item)
            self.assertIn('symbol', item)
            self.assertIn('price', item)
            self.assertIn('selected', item)

            self.assertFalse(item['selected'], "selected key should default to False.")
            self.assertEqual(
                item['image'],
                f"/web/image?model=product.product&field=image_128&id={item['id']}",
                "Image URL must be correctly formatted."
            )

        # Validate specific cross item 1
        item_1 = next(item for item in result if item['id'] == self.product_cross_1.id)
        self.assertEqual(item_1['name'], self.product_cross_1.name)
        self.assertEqual(item_1['price'], self.product_cross_1.lst_price)
        self.assertEqual(item_1['symbol'], self.product_cross_1.cost_currency_id.symbol)

    def test_13_get_cross_selling_products_archived_parent(self):
        """Test get_cross_selling_products returns empty list when parent record is archived."""
        self.cross_selling.active = False
        result = self.env['pos.cross.selling'].get_cross_selling_products(self.product_main_1.id)
        self.assertEqual(result, [], "Should return empty list when cross selling config is archived.")
        self.cross_selling.active = True

    def test_14_get_cross_selling_products_archived_line(self):
        """Test get_cross_selling_products excludes archived cross product lines."""
        line_to_archive = self.cross_selling.pos_cross_product_ids.filtered(
            lambda l: l.product_id == self.product_cross_1
        )
        line_to_archive.active = False

        result = self.env['pos.cross.selling'].get_cross_selling_products(self.product_main_1.id)
        self.assertEqual(len(result), 1, "Only active cross products should be returned.")
        self.assertEqual(result[0]['id'], self.product_cross_2.id)

        # Restore line active
        line_to_archive.active = True

    def test_15_actions_and_menus(self):
        """Test that window action and menu item exist and are correctly configured."""
        action = self.env.ref('pos_pro_cross_selling.pos_cross_selling_action', raise_if_not_found=False)
        self.assertTrue(action, "pos_cross_selling_action should exist.")
        self.assertEqual(action.res_model, 'pos.cross.selling')

        menu = self.env.ref('pos_pro_cross_selling.pos_cross_selling_menu', raise_if_not_found=False)
        self.assertTrue(menu, "pos_cross_selling_menu should exist.")
        self.assertEqual(menu.action.id, action.id)
