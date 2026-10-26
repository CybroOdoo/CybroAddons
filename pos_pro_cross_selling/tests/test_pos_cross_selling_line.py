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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosCrossSellingLine(TransactionCase):
    """Test suite for pos.cross.selling.line model."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create products
        cls.product_parent = cls.env['product.product'].create({
            'name': 'Parent Product Meal',
            'available_in_pos': True,
            'lst_price': 150.0,
        })
        cls.cross_product_1 = cls.env['product.product'].create({
            'name': 'Sauce Pack',
            'available_in_pos': True,
            'lst_price': 5.0,
        })
        cls.cross_product_2 = cls.env['product.product'].create({
            'name': 'Extra Cheese',
            'available_in_pos': True,
            'lst_price': 15.0,
        })

        # Create parent cross selling record
        cls.parent_cross = cls.env['pos.cross.selling'].create({
            'product_id': cls.product_parent.id,
            'active': True,
        })

    def test_01_create_line_directly(self):
        """Test creating a pos.cross.selling.line directly linked to a parent."""
        line = self.env['pos.cross.selling.line'].create({
            'pos_cross_product_id': self.parent_cross.id,
            'product_id': self.cross_product_1.id,
        })
        self.assertTrue(line.id, "Line should be created successfully.")
        self.assertEqual(line.pos_cross_product_id, self.parent_cross)
        self.assertEqual(line.product_id, self.cross_product_1)
        self.assertTrue(line.active, "Line active field should default to True.")

    def test_02_default_active(self):
        """Verify that default value of active field is True."""
        line = self.env['pos.cross.selling.line'].create({
            'pos_cross_product_id': self.parent_cross.id,
            'product_id': self.cross_product_2.id,
        })
        self.assertTrue(line.active, "active should default to True.")

    def test_03_line_unlink_does_not_unlink_parent(self):
        """Test deleting a line does not delete or affect parent pos.cross.selling."""
        line = self.env['pos.cross.selling.line'].create({
            'pos_cross_product_id': self.parent_cross.id,
            'product_id': self.cross_product_1.id,
        })
        line_id = line.id
        line.unlink()

        self.assertFalse(
            self.env['pos.cross.selling.line'].browse(line_id).exists(),
            "Line should be deleted."
        )
        self.assertTrue(
            self.parent_cross.exists(),
            "Parent record should remain intact when line is deleted."
        )

    def test_04_parent_relation_and_inverse(self):
        """Test relational integrity between pos.cross.selling and pos.cross.selling.line."""
        line = self.env['pos.cross.selling.line'].create({
            'pos_cross_product_id': self.parent_cross.id,
            'product_id': self.cross_product_2.id,
        })
        self.assertIn(line, self.parent_cross.pos_cross_product_ids)

    def test_05_archive_line(self):
        """Test archiving a pos.cross.selling.line record."""
        line = self.env['pos.cross.selling.line'].create({
            'pos_cross_product_id': self.parent_cross.id,
            'product_id': self.cross_product_1.id,
        })
        line.active = False
        found = self.env['pos.cross.selling.line'].search([('id', '=', line.id)])
        self.assertFalse(found, "Archived line should not be returned in default search.")

        found_all = self.env['pos.cross.selling.line'].with_context(active_test=False).search(
            [('id', '=', line.id)]
        )
        self.assertTrue(found_all, "Archived line should be returned when active_test is False.")
