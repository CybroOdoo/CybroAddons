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
from odoo.tests.common import TransactionCase

class TestPetManagement(TransactionCase):

    def setUp(self):
        super().setUp()
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Veterinarian',
            'is_veterinarian': True,
            'is_walker_sitters': True,
        })
        self.pet_type = self.env['pet.type'].create({
            'name': 'Dog'
        })
        self.vaccine_product = self.env['product.product'].create({
            'name': 'Rabies Vaccine',
            'type': 'service'
        })

    def test_01_models_field_existence(self):
        """ Test field existence and basic record creation """
        # Test HrEmployee
        self.assertTrue(self.employee.is_veterinarian)
        self.assertTrue(self.employee.is_walker_sitters)

        # Test PetType
        self.assertEqual(self.pet_type.name, 'Dog')

        # Test PetVaccines
        vaccine = self.env['pet.vaccines'].create({
            'vaccine_name': 'Anti-Rabies',
            'pet_vaccine_id': self.vaccine_product.id,
            'veterinarian_id': self.employee.id,
        })
        self.assertEqual(vaccine.vaccine_name, 'Anti-Rabies')

        # Test SittingSchedule
        schedule = self.env['sitting.schedule'].create({
            'name': 'Test Schedule',
            'attendees_ids': [(4, self.employee.id)],
        })
        self.assertEqual(schedule.name, 'Test Schedule')
        self.assertIn(self.employee, schedule.attendees_ids)

        # Test WorkingTime and WorkingHours
        work_time = self.env['working.time'].create({
            'name': 'Day Shift',
            'working_time': 8.0,
        })
        self.assertEqual(work_time.name, 'Day Shift')

        work_hour = self.env['working.hours'].create({
            'name': self.employee.id,
            'working_id': work_time.id,
            'day': 'Monday',
        })
        self.assertEqual(work_hour.name, self.employee)
        self.assertEqual(work_hour.working_id, work_time)
