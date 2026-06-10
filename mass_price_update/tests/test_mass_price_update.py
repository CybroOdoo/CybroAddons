# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestMassPriceUpdate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create categories for tests
        cls.category_1 = cls.env['product.category'].create({'name': 'Test Category 1'})
        cls.category_2 = cls.env['product.category'].create({'name': 'Test Category 2'})

        # Create products for tests
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Test Product 1',
            'categ_id': cls.category_1.id,
            'lst_price': 100.0,
            'standard_price': 50.0,
            'type': 'consu',
        })
        cls.product_2 = cls.env['product.product'].create({
            'name': 'Test Product 2',
            'categ_id': cls.category_2.id,
            'lst_price': 200.0,
            'standard_price': 100.0,
            'type': 'consu',
        })

    def test_01_onchange_apply_to_all(self):
        """Test onchange apply_to all populates all products."""
        wizard = self.env['mass.price.update'].create({'apply_to': 'selected'})
        wizard.apply_to = 'all'
        wizard._onchange_apply_to()
        
        # Check if products are correctly fetched
        self.assertIn(self.product_1, wizard.product_ids)
        self.assertIn(self.product_2, wizard.product_ids)
        # Verify category_ids and line_ids are cleared
        self.assertFalse(wizard.category_ids)
        self.assertFalse(wizard.line_ids)

    def test_02_onchange_apply_to_category(self):
        """Test onchange apply_to category populates products based on category."""
        wizard = self.env['mass.price.update'].create({
            'apply_to': 'selected',
            'category_ids': [(6, 0, self.category_1.ids)],
        })
        wizard.apply_to = 'category'
        wizard._onchange_apply_to()
        
        # Should include product_1 (in category_1) but not product_2
        self.assertIn(self.product_1, wizard.product_ids)
        self.assertNotIn(self.product_2, wizard.product_ids)
        # Verify line_ids are cleared
        self.assertFalse(wizard.line_ids)

    def test_03_onchange_apply_to_selected(self):
        """Test onchange apply_to selected clears fields."""
        wizard = self.env['mass.price.update'].create({
            'apply_to': 'category',
            'category_ids': [(6, 0, self.category_1.ids)],
            'product_ids': [(6, 0, self.product_1.ids)],
        })
        wizard.apply_to = 'selected'
        wizard._onchange_apply_to()
        
        # Everything should be cleared
        self.assertFalse(wizard.product_ids)
        self.assertFalse(wizard.category_ids)
        self.assertFalse(wizard.line_ids)

    def test_04_onchange_product_ids(self):
        """Test onchange product_ids populates line_ids correctly."""
        wizard = self.env['mass.price.update'].create({})
        wizard.product_ids = [(6, 0, (self.product_1 + self.product_2).ids)]
        wizard._onchange_product_ids()
        
        products_in_lines = wizard.line_ids.mapped('product_id')
        self.assertIn(self.product_1, products_in_lines)
        self.assertIn(self.product_2, products_in_lines)
        self.assertEqual(len(wizard.line_ids), 2)

    def test_05_onchange_category_ids(self):
        """Test onchange category_ids populates product_ids and line_ids."""
        wizard = self.env['mass.price.update'].create({})
        wizard.category_ids = [(6, 0, self.category_1.ids)]
        wizard._onchange_category_ids()
        
        # Should populate products from the selected categories
        self.assertIn(self.product_1, wizard.product_ids)
        self.assertNotIn(self.product_2, wizard.product_ids)
        
        products_in_lines = wizard.line_ids.mapped('product_id')
        self.assertIn(self.product_1, products_in_lines)
        self.assertNotIn(self.product_2, products_in_lines)

    def test_06_action_change_price_validations(self):
        """Test validations in action_change_price."""
        wizard_cat = self.env['mass.price.update'].create({
            'apply_to': 'category',
            'category_ids': [(6, 0, self.category_1.ids)],
            'change': 0.1,
            # No product_ids
        })
        with self.assertRaisesRegex(UserError, "Please select any category with products"):
            wizard_cat.action_change_price()

        wizard_sel = self.env['mass.price.update'].create({
            'apply_to': 'selected',
            'change': 0.1,
            # No product_ids
        })
        with self.assertRaisesRegex(UserError, "Please select any product"):
            wizard_sel.action_change_price()

        wizard_no_change = self.env['mass.price.update'].create({
            'apply_to': 'selected',
            'product_ids': [(6, 0, self.product_1.ids)],
            'change': 0.0,
        })
        with self.assertRaisesRegex(UserError, "Please enter the change in percentage"):
            wizard_no_change.action_change_price()

    def test_07_action_change_price_add(self):
        """Test action_change_price with add type and price apply."""
        wizard = self.env['mass.price.update'].create({
            'apply_to': 'selected',
            'apply_on': 'price',
            'apply_type': 'add',
            'change': 0.10,  # Add 10%
            'product_ids': [(6, 0, self.product_1.ids)],
        })
        res = wizard.action_change_price()
        
        # Original price is 100.0, adding 10% makes it 110.0
        self.assertAlmostEqual(self.product_1.lst_price, 110.0)
        
        # Check action return
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'display_notification')

    def test_08_action_change_price_reduce(self):
        """Test action_change_price with reduce type and cost apply."""
        wizard = self.env['mass.price.update'].create({
            'apply_to': 'selected',
            'apply_on': 'cost',
            'apply_type': 'reduce',
            'change': 0.10,  # Reduce 10%
            'product_ids': [(6, 0, self.product_1.ids)],
        })
        wizard.action_change_price()
        
        # Original cost is 50.0, reducing by 10% makes it 45.0
        self.assertAlmostEqual(self.product_1.product_tmpl_id.standard_price, 45.0)

    def test_09_compute_new_price_cost(self):
        """Test compute field logic for new price and new cost in lines."""
        wizard = self.env['mass.price.update'].create({
            'apply_to': 'selected',
            'apply_on': 'price',
            'apply_type': 'add',
            'change': 0.20,  # Add 20%
            'product_ids': [(6, 0, self.product_1.ids)],
        })
        
        line = self.env['change.price.line'].create({
            'mass_price_update_id': wizard.id,
            'product_id': self.product_1.id,
        })
        
        # Original price is 100.0, adding 20% makes it 120.0
        self.assertAlmostEqual(line.new_price, 120.0)
        self.assertFalse(line.new_cost)

        wizard.write({
            'apply_on': 'cost',
            'apply_type': 'reduce',
            'change': 0.20,  # Reduce 20%
        })
        
        # Invalidate cache to force recompute since wizard fields have changed
        line.invalidate_recordset(['new_price', 'new_cost'])
        
        # Original cost is 50.0, reducing by 20% makes it 40.0
        self.assertFalse(line.new_price)
        self.assertAlmostEqual(line.new_cost, 40.0)
