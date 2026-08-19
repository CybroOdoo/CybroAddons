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
from odoo.exceptions import ValidationError
from odoo import fields, Command


class TestAnimalGrooming(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestAnimalGrooming, cls).setUpClass()

        # Create basic data needed for tests
        cls.owner = cls.env['res.partner'].create({
            'name': 'Grooming Test Owner',
            'phone': '9876543210',
            'email': 'groomingowner@test.com'
        })

        cls.animal_type = cls.env['animal.types'].create({
            'name': 'Test Grooming Cat'
        })

        cls.patient = cls.env['res.patient'].create({
            'name': 'Mittens',
            'pet_type_id': cls.animal_type.id,
            'gender': 'female',
            'age': 2,
            'owner_name_id': cls.owner.id,
        })

        cls.grooming_service = cls.env['product.product'].create({
            'name': 'Full Spa & Deshedding',
            'type': 'service',
            'is_grooming_product': True,
            'list_price': 50.0
        })

        cls.groomer = cls.env['res.partner'].create({
            'name': 'Groomer Jane',
        })

    def test_01_grooming_creation(self):
        """Test animal grooming creation and auto sequence."""
        grooming = self.env['animal.grooming'].create({
            'patient_name_id': self.patient.id,
            'grooming_employee_id': self.groomer.id,
            'appointment_date': fields.Date.today(),
        })

        self.assertTrue(grooming.grooming_no, "Grooming No should be generated")
        self.assertEqual(grooming.state, 'draft', "Default state should be draft")
        self.assertEqual(grooming.patient_name_id, self.patient, "Patient should match")

    def test_02_grooming_total_computation(self):
        """Test computation of grooming total."""
        grooming = self.env['animal.grooming'].create({
            'patient_name_id': self.patient.id,
            'grooming_employee_id': self.groomer.id,
            'grooming_line_ids': [Command.create({
                'service_id': self.grooming_service.id,
                'description': 'Spa',
            })]
        })
        self.assertEqual(grooming.grooming_total, 50.0, "Grooming total should be 50.0")

    def test_03_create_invoice_without_services(self):
        """Test validation error when creating invoice without services."""
        grooming = self.env['animal.grooming'].create({
            'patient_name_id': self.patient.id,
            'grooming_employee_id': self.groomer.id,
        })

        with self.assertRaises(ValidationError):
            grooming.action_create_invoice()

    def test_04_create_invoice_with_services(self):
        """Test successful invoice creation."""
        grooming = self.env['animal.grooming'].create({
            'patient_name_id': self.patient.id,
            'grooming_employee_id': self.groomer.id,
            'grooming_line_ids': [Command.create({
                'service_id': self.grooming_service.id,
            })]
        })

        # Create Invoice
        action = grooming.action_create_invoice()

        self.assertTrue(grooming.is_invoice, "is_invoice should be True")
        self.assertTrue(grooming.grooming_invoice_id, "Invoice should be created and linked")

        invoice = grooming.grooming_invoice_id
        self.assertEqual(invoice.move_type, 'out_invoice', "Invoice type should be out_invoice")
        self.assertEqual(invoice.partner_id, self.owner, "Invoice should be billed to owner")
        self.assertEqual(len(invoice.invoice_line_ids), 1, "Invoice should have 1 line")
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 50.0, "Invoice line price should be 50.0")