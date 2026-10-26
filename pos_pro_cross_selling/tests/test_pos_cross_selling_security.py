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
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPosCrossSellingSecurity(TransactionCase):
    """Test suite for security and access rights on pos.cross.selling
    and pos.cross.selling.line models.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_user = cls.env.ref('base.group_user')
        group_pos_manager = cls.env.ref('point_of_sale.group_pos_manager')

        # Create POS Manager user
        cls.user_manager = cls.env['res.users'].create({
            'name': 'POS Cross Selling Manager',
            'login': 'pos_cross_selling_manager_test',
            'email': 'pos_manager@test.com',
            'group_ids': [(6, 0, [group_user.id, group_pos_manager.id])],
        })

        # Create standard internal user without POS Manager rights
        cls.user_internal = cls.env['res.users'].create({
            'name': 'Standard Internal User',
            'login': 'pos_cross_selling_user_test',
            'email': 'pos_internal@test.com',
            'group_ids': [(6, 0, [group_user.id])],
        })

        # Create products for testing
        cls.product_1 = cls.env['product.product'].create({
            'name': 'Main Product Test',
            'available_in_pos': True,
            'lst_price': 50.0,
        })
        cls.cross_product = cls.env['product.product'].create({
            'name': 'Cross Product Test',
            'available_in_pos': True,
            'lst_price': 10.0,
        })

        # Pre-create a cross-selling record as admin
        cls.cross_record = cls.env['pos.cross.selling'].create({
            'product_id': cls.product_1.id,
            'pos_cross_product_ids': [
                (0, 0, {'product_id': cls.cross_product.id}),
            ],
        })
        cls.cross_line = cls.cross_record.pos_cross_product_ids[0]

    def test_01_manager_crud_pos_cross_selling(self):
        """Test that POS Manager has full CRUD access on pos.cross.selling."""
        product_new = self.env['product.product'].create({
            'name': 'Manager Product',
            'available_in_pos': True,
        })
        manager_cross = self.env['pos.cross.selling'].with_user(self.user_manager)

        # Create
        record = manager_cross.create({
            'product_id': product_new.id,
        })
        self.assertTrue(record.id, "POS Manager should be able to create pos.cross.selling.")

        # Read
        read_data = record.read(['product_id', 'active'])
        self.assertTrue(read_data, "POS Manager should be able to read pos.cross.selling.")

        # Write
        record.write({'active': False})
        self.assertFalse(record.active, "POS Manager should be able to write to pos.cross.selling.")

        # Unlink
        record_id = record.id
        record.unlink()
        self.assertFalse(
            self.env['pos.cross.selling'].browse(record_id).exists(),
            "POS Manager should be able to unlink pos.cross.selling."
        )

    def test_02_manager_crud_pos_cross_selling_line(self):
        """Test that POS Manager has full CRUD access on pos.cross.selling.line."""
        product_new = self.env['product.product'].create({
            'name': 'Manager Line Product',
            'available_in_pos': True,
        })
        manager_line = self.env['pos.cross.selling.line'].with_user(self.user_manager)

        # Create
        line = manager_line.create({
            'pos_cross_product_id': self.cross_record.id,
            'product_id': product_new.id,
        })
        self.assertTrue(line.id, "POS Manager should be able to create pos.cross.selling.line.")

        # Read
        read_data = line.read(['product_id', 'active'])
        self.assertTrue(read_data, "POS Manager should be able to read pos.cross.selling.line.")

        # Write
        line.write({'active': False})
        self.assertFalse(line.active, "POS Manager should be able to write to pos.cross.selling.line.")

        # Unlink
        line_id = line.id
        line.unlink()
        self.assertFalse(
            self.env['pos.cross.selling.line'].browse(line_id).exists(),
            "POS Manager should be able to unlink pos.cross.selling.line."
        )

    def test_03_internal_user_can_read(self):
        """Test that standard internal user can read pos.cross.selling and lines."""
        internal_cross = self.cross_record.with_user(self.user_internal)
        read_data = internal_cross.read(['product_id', 'active'])
        self.assertTrue(read_data, "Internal user should be able to read pos.cross.selling.")

        internal_line = self.cross_line.with_user(self.user_internal)
        read_line_data = internal_line.read(['product_id', 'active'])
        self.assertTrue(read_line_data, "Internal user should be able to read pos.cross.selling.line.")

    def test_04_internal_user_cannot_create_pos_cross_selling(self):
        """Test that standard internal user cannot create pos.cross.selling."""
        product_new = self.env['product.product'].create({
            'name': 'Unauthorized Product',
            'available_in_pos': True,
        })
        internal_cross = self.env['pos.cross.selling'].with_user(self.user_internal)
        with self.assertRaises(AccessError):
            internal_cross.create({
                'product_id': product_new.id,
            })

    def test_05_internal_user_cannot_write_pos_cross_selling(self):
        """Test that standard internal user cannot write to pos.cross.selling."""
        internal_cross = self.cross_record.with_user(self.user_internal)
        with self.assertRaises(AccessError):
            internal_cross.write({'active': False})

    def test_06_internal_user_cannot_unlink_pos_cross_selling(self):
        """Test that standard internal user cannot delete pos.cross.selling."""
        internal_cross = self.cross_record.with_user(self.user_internal)
        with self.assertRaises(AccessError):
            internal_cross.unlink()

    def test_07_internal_user_cannot_create_pos_cross_selling_line(self):
        """Test that standard internal user cannot create pos.cross.selling.line."""
        product_new = self.env['product.product'].create({
            'name': 'Unauthorized Line Product',
            'available_in_pos': True,
        })
        internal_line = self.env['pos.cross.selling.line'].with_user(self.user_internal)
        with self.assertRaises(AccessError):
            internal_line.create({
                'pos_cross_product_id': self.cross_record.id,
                'product_id': product_new.id,
            })

    def test_08_internal_user_cannot_write_pos_cross_selling_line(self):
        """Test that standard internal user cannot write to pos.cross.selling.line."""
        internal_line = self.cross_line.with_user(self.user_internal)
        with self.assertRaises(AccessError):
            internal_line.write({'active': False})

    def test_09_internal_user_cannot_unlink_pos_cross_selling_line(self):
        """Test that standard internal user cannot delete pos.cross.selling.line."""
        internal_line = self.cross_line.with_user(self.user_internal)
        with self.assertRaises(AccessError):
            internal_line.unlink()
