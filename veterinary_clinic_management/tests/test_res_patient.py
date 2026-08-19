# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestResPatient(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestResPatient, cls).setUpClass()

        cls.owner = cls.env['res.partner'].create({
            'name': 'Patient Test Owner',
            'phone': '1122334455',
            'email': 'patientowner@test.com'
        })

        cls.animal_type = cls.env['animal.types'].create({
            'name': 'Dog'
        })
        
        cls.breed_type = cls.env['breed.types'].create({
            'name': 'Beagle'
        })

    def test_01_patient_creation(self):
        """Test patient creation and sequence generation."""
        patient = self.env['res.patient'].create({
            'name': 'Snoopy',
            'pet_type_id': self.animal_type.id,
            'breed_id': self.breed_type.id,
            'gender': 'male',
            'age': 5,
            'owner_name_id': self.owner.id,
        })

        self.assertTrue(patient.number, "Patient sequence should be generated")
        self.assertEqual(patient.name, 'Snoopy', "Patient name should match")
        self.assertEqual(patient.pet_type_id.name, 'Dog', "Animal type should match")
        self.assertEqual(patient.owner_name_id.name, 'Patient Test Owner', "Owner should match")
        self.assertEqual(patient.gender, 'male', "Gender should match")
