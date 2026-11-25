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
class TestHrEmployee(TransactionCase):

    def test_01_employee_flags(self):
        """ Test hr.employee custom flags for veterinarian and walker/sitter
        """
        vet = self.env['hr.employee'].create({
            'name': 'Dr. Vet',
            'is_veterinarian': True,
            'is_walker_sitters': False,
        })
        sitter = self.env['hr.employee'].create({
            'name': 'Sam Walker',
            'is_veterinarian': False,
            'is_walker_sitters': True,
        })

        self.assertTrue(vet.is_veterinarian)
        self.assertFalse(vet.is_walker_sitters)
        self.assertFalse(sitter.is_veterinarian)
        self.assertTrue(sitter.is_walker_sitters)

        vets = self.env['hr.employee'].search(
            [('is_veterinarian', '=', True)]
        )
        sitters = self.env['hr.employee'].search(
            [('is_walker_sitters', '=', True)]
        )
        self.assertIn(vet, vets)
        self.assertNotIn(sitter, vets)
        self.assertIn(sitter, sitters)
        self.assertNotIn(vet, sitters)
