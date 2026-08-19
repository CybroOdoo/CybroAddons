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
from datetime import timedelta


class TestCaseAppointments(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaseAppointments, cls).setUpClass()

        # Create basic data needed for tests
        cls.owner = cls.env['res.partner'].create({
            'name': 'Test Owner',
            'phone': '1234567890',
            'email': 'owner@test.com'
        })

        cls.animal_type = cls.env['animal.types'].create({
            'name': 'Dog'
        })

        cls.patient = cls.env['res.patient'].create({
            'name': 'Buddy',
            'pet_type_id': cls.animal_type.id,
            'gender': 'male',
            'age': 3,
            'owner_name_id': cls.owner.id,
        })

        cls.doctor = cls.env['veterinary.employees'].create({
            'name': 'Dr. Smith',
            'staff': 'doctor',
            'consultancy_charges': 500.0,
        })

        cls.nurse = cls.env['veterinary.employees'].create({
            'name': 'Nurse Joy',
            'staff': 'nurse',
        })

        cls.room = cls.env['room.details'].create({
            'name': 'Room 101',
            'charge': 100.0,
        })

        cls.treatment_service = cls.env['product.product'].create({
            'name': 'Treatment',
            'type': 'service',
            'is_medical_bill_product': True,
            'list_price': 100.0
        })

        cls.consultancy_service = cls.env['product.product'].create({
            'name': 'Consultancy',
            'type': 'service',
            'is_medical_bill_product': True,
            'list_price': 500.0
        })

        cls.admit_service = cls.env['product.product'].create({
            'name': 'Admit',
            'type': 'service',
            'is_medical_bill_product': True,
            'list_price': 100.0
        })

    def test_01_appointment_creation(self):
        """Test case appointment creation and auto sequence."""
        appointment = self.env['case.appointments'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'nurse_id': self.nurse.id,
            'appointment_date': fields.Date.today(),
        })

        self.assertTrue(appointment.case_no, "Case No should be generated")
        self.assertEqual(appointment.state, 'draft', "Default state should be draft")
        self.assertEqual(appointment.owner_id, self.owner, "Owner should be related to patient")

    def test_02_appointment_date_validation(self):
        """Test validation for past appointment date."""
        past_date = fields.Date.today() - timedelta(days=2)
        with self.assertRaises(ValidationError):
            appointment = self.env['case.appointments'].create({
                'patient_id': self.patient.id,
                'doctor_id': self.doctor.id,
                'appointment_date': past_date,
            })
            appointment._onchange_appointment_date()

    def test_03_admit_amount_computation(self):
        """Test computation of total admit amount."""
        appointment = self.env['case.appointments'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'room_id': self.room.id,
            'total_hours': 24,
        })
        # Note: total_amount is a compute field that depends on total_hours and room_charge
        self.assertEqual(appointment.total_amount, 2400.0, "Total amount should be 24 * 100")

    def test_04_treatment_total_computation(self):
        """Test computation of treatment total."""
        appointment = self.env['case.appointments'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'treatment_line_ids': [Command.create({
                'description': 'Test Treatment 1',
                'charges': 200.0,
            }), Command.create({
                'description': 'Test Treatment 2',
                'charges': 300.0,
            })]
        })
        self.assertEqual(appointment.treatment_total, 500.0, "Treatment total should be 500")

    def test_05_state_transitions(self):
        """Test action_confirm and action_cancel."""
        appointment = self.env['case.appointments'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
        })

        appointment.action_confirm()
        self.assertEqual(appointment.state, 'in-consultation', "State should be in-consultation")

        appointment.action_cancel()
        self.assertEqual(appointment.state, 'cancel', "State should be cancel")

    def test_06_medical_bill_and_invoice(self):
        """Test medical bill line addition and invoice creation."""
        appointment = self.env['case.appointments'].create({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'room_id': self.room.id,
            'total_hours': 10,
        })

        # Add a medical bill detail
        bill_line_1 = self.env['medical.bill.details'].create({
            'medical_bill_id': appointment.id,
            'service_type_id': self.consultancy_service.id,
        })
        # Trigger onchange manually as it's a test environment
        bill_line_1._onchange_service_type()

        bill_line_2 = self.env['medical.bill.details'].create({
            'medical_bill_id': appointment.id,
            'service_type_id': self.admit_service.id,
        })
        bill_line_2._onchange_service_type()

        self.assertEqual(bill_line_1.amount, 500.0, "Consultancy charge should be fetched from doctor")
        self.assertEqual(bill_line_2.amount, 1000.0, "Admit charge should be total_hours * room_charge (10 * 100)")

        # Create Invoice
        appointment.action_create_invoice()

        self.assertTrue(appointment.is_invoice, "is_invoice should be True")
        self.assertTrue(appointment.medical_bill_invoice_id, "Invoice should be created and linked")

        invoice = appointment.medical_bill_invoice_id
        self.assertEqual(invoice.move_type, 'out_invoice', "Invoice type should be out_invoice")
        self.assertEqual(invoice.partner_id, self.owner, "Invoice should be billed to owner")
        self.assertEqual(len(invoice.invoice_line_ids), 2, "Invoice should have 2 lines")