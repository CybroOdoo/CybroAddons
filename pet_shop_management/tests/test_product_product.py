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
from datetime import date, timedelta
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestProductProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Pet Customer Test',
            'email': 'customer@example.com',
        })
        cls.pet_type = cls.env['pet.type'].create({
            'name': 'Golden Retriever',
        })

    def test_01_pet_creation_and_sequence(self):
        """ Test pet creation, sequence generation, and age calculation """
        today = date.today()
        birth_date = today - timedelta(days=730)  # ~2 years ago

        pet = self.env['product.product'].create({
            'name': 'Buddy',
            'is_pet': True,
            'dob': birth_date,
            'sex': 'male',
            'pet_type_id': self.pet_type.id,
            'customer_id': self.partner.id,
        })

        self.assertTrue(pet.pet_seq)
        self.assertNotEqual(pet.pet_seq, 'New')
        self.assertGreaterEqual(pet.age, 1.0)
        self.assertGreater(pet.month, 20)
        self.assertEqual(
            pet._get_report_base_filename(), f"Pet - {pet.pet_seq}"
        )

    def test_02_pet_age_without_dob(self):
        """ Test age computation when DOB is not provided """
        pet = self.env['product.product'].create({
            'name': 'Nameless Pup',
            'is_pet': True,
            'dob': False,
        })
        self.assertFalse(pet.age)
        self.assertFalse(pet.month)

    def test_03_create_sale_order_no_partner(self):
        """ Test sale order creation fails when no customer/partner is set """
        pet = self.env['product.product'].create({
            'name': 'Unassigned Dog',
            'is_pet': True,
        })
        with self.assertRaises(UserError):
            pet.create_sale_order()

    def test_04_create_sale_order_pet_zero_qty(self):
        """ Test sale order creation fails when pet quantity is 0 """
        pet = self.env['product.product'].create({
            'name': 'Out of Stock Pet',
            'is_pet': True,
            'customer_id': self.partner.id,
        })
        with self.assertRaises(UserError):
            pet.create_sale_order()

    def test_05_create_sale_order_pet_with_stock(self):
        """ Test sale order creation succeeds when pet has stock """
        pet = self.env['product.product'].create({
            'name': 'In Stock Pet',
            'is_pet': True,
            'is_storable': True,
            'customer_id': self.partner.id,
            'list_price': 500.0,
        })
        # Update stock quantity
        stock_location = self.env.ref('stock.stock_location_stock')
        self.env['stock.quant']._update_available_quantity(
            pet, stock_location, 1.0
        )

        action = pet.create_sale_order()
        self.assertEqual(action.get('res_model'), 'sale.order')
        sale = self.env['sale.order'].browse(action.get('res_id'))
        self.assertTrue(sale.exists())
        self.assertEqual(sale.partner_id, self.partner)
        self.assertEqual(len(sale.order_line), 1)
        self.assertEqual(sale.order_line.product_id, pet)
        self.assertEqual(sale.order_line.product_uom_qty, 1.0)
        self.assertEqual(sale.order_line.price_unit, 500.0)

    def test_06_create_sale_order_service(self):
        """ Test sale order creation for pet service """
        service = self.env['product.product'].create({
            'name': 'Dog Grooming Service',
            'is_pet_service': True,
            'customer_id': self.partner.id,
            'list_price': 60.0,
        })
        action = service.create_sale_order()
        self.assertEqual(action.get('res_model'), 'sale.order')
        sale = self.env['sale.order'].browse(action.get('res_id'))
        self.assertTrue(sale.exists())
        self.assertEqual(sale.partner_id, self.partner)
        self.assertEqual(sale.order_line.product_id, service)
        self.assertEqual(sale.order_line.price_unit, 60.0)

    def test_07_create_sale_order_regular_product_fails(self):
        """ Test sale order creation fails for non-pet and non-service """
        product = self.env['product.product'].create({
            'name': 'Dog Bowl Toy',
            'is_pet': False,
            'is_pet_service': False,
            'customer_id': self.partner.id,
        })
        with self.assertRaises(UserError):
            product.create_sale_order()
