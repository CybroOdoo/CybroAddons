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
class TestCarryBagPos(TransactionCase):
    """Test suite for carry_bag_pos module.
    Covers pos.config, res.config.settings, bag category filtering,
    order line creation, and view architecture.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company

        # Set up POS categories
        cls.bag_category = cls.env['pos.category'].create({
            'name': 'Carry Bags',
        })
        cls.other_category = cls.env['pos.category'].create({
            'name': 'Drinks',
        })

        # Set up products
        cls.bag_product_small = cls.env['product.product'].create({
            'name': 'Small Paper Bag',
            'available_in_pos': True,
            'list_price': 0.15,
            'pos_categ_ids': [(6, 0, [cls.bag_category.id])],
        })
        cls.bag_product_large = cls.env['product.product'].create({
            'name': 'Large Cloth Bag',
            'available_in_pos': True,
            'list_price': 0.50,
            'pos_categ_ids': [(6, 0, [cls.bag_category.id])],
        })
        cls.regular_product = cls.env['product.product'].create({
            'name': 'Apple Juice',
            'available_in_pos': True,
            'list_price': 2.50,
            'pos_categ_ids': [(6, 0, [cls.other_category.id])],
        })

        # Set up POS config
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test Bag POS Shop',
            'is_bag_charges': True,
            'bag_category_id': cls.bag_category.id,
        })

    def test_01_pos_config_fields(self):
        """Test that the custom fields exist and hold the correct values on pos.config."""
        self.assertTrue(
            hasattr(self.pos_config, 'is_bag_charges'),
            "pos.config should have 'is_bag_charges' field."
        )
        self.assertTrue(
            hasattr(self.pos_config, 'bag_category_id'),
            "pos.config should have 'bag_category_id' field."
        )
        self.assertTrue(self.pos_config.is_bag_charges)
        self.assertEqual(self.pos_config.bag_category_id, self.bag_category)

    def test_02_pos_config_defaults(self):
        """Test the default values of a new pos.config without bag charges."""
        new_config = self.env['pos.config'].create({
            'name': 'Default Bag POS Shop',
        })
        self.assertFalse(new_config.is_bag_charges)
        self.assertFalse(new_config.bag_category_id)

    def test_03_pos_config_update_values(self):
        """Test updating bag charges and category on pos.config."""
        config = self.env['pos.config'].create({
            'name': 'Update Bag POS Shop',
        })
        config.write({
            'is_bag_charges': True,
            'bag_category_id': self.bag_category.id,
        })
        self.assertTrue(config.is_bag_charges)
        self.assertEqual(config.bag_category_id.id, self.bag_category.id)

        # Disable bag charges
        config.write({
            'is_bag_charges': False,
            'bag_category_id': False,
        })
        self.assertFalse(config.is_bag_charges)
        self.assertFalse(config.bag_category_id)

    def test_04_res_config_settings_related_fields(self):
        """Test that res.config.settings properly reads and writes to pos.config."""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
        })

        # Verify initial values related to pos_config
        self.assertEqual(settings.is_pos_bag_charges, self.pos_config.is_bag_charges)
        self.assertEqual(settings.pos_bag_category_id, self.pos_config.bag_category_id)

        # Update via settings write
        settings.write({
            'is_pos_bag_charges': False,
            'pos_bag_category_id': False,
        })

        self.assertFalse(self.pos_config.is_bag_charges)
        self.assertFalse(self.pos_config.bag_category_id)

        # Re-enable via settings write
        settings.write({
            'is_pos_bag_charges': True,
            'pos_bag_category_id': self.bag_category.id,
        })

        self.assertTrue(self.pos_config.is_bag_charges)
        self.assertEqual(self.pos_config.bag_category_id, self.bag_category)

    def test_05_bag_products_category_filtering(self):
        """Test filtering products assigned to the bag category."""
        category_id = self.pos_config.bag_category_id.id
        bag_products = self.env['product.product'].search([
            ('available_in_pos', '=', True),
            ('pos_categ_ids', 'in', category_id),
        ])

        self.assertIn(self.bag_product_small, bag_products)
        self.assertIn(self.bag_product_large, bag_products)
        self.assertNotIn(self.regular_product, bag_products)

    def test_06_add_bag_to_pos_order(self):
        """Simulate adding a bag line to a POS order."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        order = self.env['pos.order'].create({
            'company_id': self.company.id,
            'session_id': session.id,
            'lines': [
                (0, 0, {
                    'product_id': self.regular_product.id,
                    'price_unit': self.regular_product.lst_price,
                    'qty': 1.0,
                    'price_subtotal': self.regular_product.lst_price,
                    'price_subtotal_incl': self.regular_product.lst_price,
                }),
            ],
            'amount_tax': 0.0,
            'amount_total': self.regular_product.lst_price,
            'amount_paid': self.regular_product.lst_price,
            'amount_return': 0.0,
        })

        self.assertEqual(len(order.lines), 1)

        # Simulate adding a bag line
        bag_line = self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.bag_product_small.id,
            'qty': 1.0,
            'price_unit': self.bag_product_small.lst_price,
            'price_subtotal': self.bag_product_small.lst_price,
            'price_subtotal_incl': self.bag_product_small.lst_price,
        })

        self.assertEqual(len(order.lines), 2)
        self.assertEqual(bag_line.product_id, self.bag_product_small)
        self.assertEqual(bag_line.price_unit, 0.15)
        self.assertEqual(bag_line.qty, 1.0)
        self.assertEqual(bag_line.price_subtotal, 0.15)

    def test_07_multiple_bags_addition(self):
        """Test adding multiple bags to an order."""
        session = self.env['pos.session'].create({
            'config_id': self.pos_config.id,
        })

        order = self.env['pos.order'].create({
            'company_id': self.company.id,
            'session_id': session.id,
            'lines': [
                (0, 0, {
                    'product_id': self.regular_product.id,
                    'price_unit': self.regular_product.lst_price,
                    'qty': 2.0,
                    'price_subtotal': self.regular_product.lst_price * 2,
                    'price_subtotal_incl': self.regular_product.lst_price * 2,
                }),
            ],
            'amount_tax': 0.0,
            'amount_total': self.regular_product.lst_price * 2,
            'amount_paid': self.regular_product.lst_price * 2,
            'amount_return': 0.0,
        })

        # Add 2 Small Paper Bags and 1 Large Cloth Bag
        self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.bag_product_small.id,
            'qty': 2.0,
            'price_unit': self.bag_product_small.lst_price,
            'price_subtotal': self.bag_product_small.lst_price * 2,
            'price_subtotal_incl': self.bag_product_small.lst_price * 2,
        })
        self.env['pos.order.line'].create({
            'order_id': order.id,
            'product_id': self.bag_product_large.id,
            'qty': 1.0,
            'price_unit': self.bag_product_large.lst_price,
            'price_subtotal': self.bag_product_large.lst_price,
            'price_subtotal_incl': self.bag_product_large.lst_price,
        })

        self.assertEqual(len(order.lines), 3)
        bag_lines = order.lines.filtered(
            lambda l: l.product_id.id in (self.bag_product_small.id, self.bag_product_large.id)
        )
        self.assertEqual(len(bag_lines), 2)
        total_bag_amount = sum(bag_lines.mapped('price_subtotal'))
        self.assertAlmostEqual(total_bag_amount, (0.15 * 2) + 0.50)

    def test_08_res_config_settings_view_architecture(self):
        """Test that the res.config.settings inherited view exists and contains fields."""
        view = self.env.ref('carry_bag_pos.res_config_settings_view_form', raise_if_not_found=False)
        self.assertTrue(view, "Inherited view carry_bag_pos.res_config_settings_view_form should exist.")
        self.assertEqual(view.model, 'res.config.settings')
        self.assertIn('is_pos_bag_charges', view.arch)
        self.assertIn('pos_bag_category_id', view.arch)

    def test_09_get_bag_stock(self):
        """The stock helper returns a number for POS bag products only."""
        template_ids = (
            self.bag_product_small.product_tmpl_id
            | self.regular_product.product_tmpl_id
        ).ids
        stock = self.pos_config.get_bag_stock(template_ids)
        self.assertIn(self.bag_product_small.product_tmpl_id.id, stock)
        self.assertIsInstance(stock[self.bag_product_small.product_tmpl_id.id], float)
