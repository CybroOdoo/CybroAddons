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


@tagged('post_install', '-at_install', 'pet_shop_management')
class TestPetVaccines(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pet = cls.env['product.product'].create({
            'name': 'Charlie',
            'is_pet': True,
        })
        cls.vet = cls.env['hr.employee'].create({
            'name': 'Dr. Doolittle',
            'is_veterinarian': True,
        })

    def test_01_vaccine_creation_and_fields(self):
        """ Test pet.vaccines record linked to a pet product """
        today = date.today()
        exp_date = today + timedelta(days=365)

        vaccine = self.env['pet.vaccines'].create({
            'pet_vaccine_id': self.pet.id,
            'vaccine_name': 'Rabies Vaccine',
            'date': today,
            'date_exp': exp_date,
            'veterinarian_id': self.vet.id,
        })

        self.assertTrue(vaccine.exists())
        self.assertEqual(vaccine.display_name, 'Rabies Vaccine')
        self.assertEqual(vaccine.pet_vaccine_id, self.pet)
        self.assertEqual(vaccine.veterinarian_id, self.vet)
        self.assertEqual(vaccine.date, today)
        self.assertEqual(vaccine.date_exp, exp_date)

        # Verify pet.vaccines appears in pet's One2many
        self.assertIn(vaccine, self.pet.pet_vaccines_ids)
