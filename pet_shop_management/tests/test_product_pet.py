# -*- coding: utf-8 -*-
##############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import date, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError

class TestProductPet(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.pet_type = self.env['pet.type'].create({'name': 'Cat'})
        self.pet = self.env['product.product'].create({
            'name': 'Test Pet',
            'is_pet': True,
            'is_storable': True,
            'dob': date.today() - timedelta(days=400), # 1 year and some months old
            'pet_type_id': self.pet_type.id,
            'partner_id': self.partner.id,
            'list_price': 100.0,
        })
        self.pet_service = self.env['product.product'].create({
            'name': 'Test Pet Service',
            'is_pet_service': True,
            'partner_id': self.partner.id,
            'list_price': 50.0,
        })

    def test_01_compute_age(self):
        """ Test age computation logic """
        self.assertEqual(self.pet.age, 1)
        self.assertEqual(self.pet.month, 13) # 400 // 30 approx 13

        self.pet.dob = False
        self.pet._compute_age()
        self.assertFalse(self.pet.age)
        self.assertFalse(self.pet.month)

    def test_02_create_sale_order_pet(self):
        """ Test sale order creation for pet """
        # Should raise UserError if quantity is zero
        with self.assertRaises(UserError):
            self.pet.create_sale_order()

        # Add inventory
        warehouse = self.env['stock.warehouse'].search([], limit=1)
        self.env['stock.quant']._update_available_quantity(self.pet, warehouse.lot_stock_id, 1)

        action = self.pet.create_sale_order()
        self.assertEqual(action['res_model'], 'sale.order')
        sale_order = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(sale_order.partner_id, self.partner)
        self.assertEqual(len(sale_order.order_line), 1)
        self.assertEqual(sale_order.order_line.product_id, self.pet)

    def test_03_create_sale_order_service(self):
        """ Test sale order creation for pet service """
        action = self.pet_service.create_sale_order()
        self.assertEqual(action['res_model'], 'sale.order')
        sale_order = self.env['sale.order'].browse(action['res_id'])
        self.assertEqual(sale_order.partner_id, self.partner)
        self.assertEqual(len(sale_order.order_line), 1)
        self.assertEqual(sale_order.order_line.product_id, self.pet_service)

    def test_04_create_sale_order_error(self):
        """ Test sale order creation error for non-pet product """
        other_product = self.env['product.product'].create({'name': 'Other'})
        with self.assertRaises(UserError):
            other_product.create_sale_order()

    def test_05_sequence_generation(self):
        """ Test pet sequence generation """
        self.assertNotEqual(self.pet.pet_seq, 'New')
        self.assertTrue(self.pet.pet_seq.startswith('PS/PT/')) # Prefix from ir_sequence_data.xml
