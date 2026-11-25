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


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestPetType(TransactionCase):

    def test_01_pet_type_crud(self):
        """ Test pet.type creation and search """
        pet_type = self.env['pet.type'].create({
            'name': 'Persian Cat',
        })
        self.assertTrue(pet_type.exists())
        self.assertEqual(pet_type.name, 'Persian Cat')

        found = self.env['pet.type'].search([('name', '=', 'Persian Cat')])
        self.assertIn(pet_type, found)
