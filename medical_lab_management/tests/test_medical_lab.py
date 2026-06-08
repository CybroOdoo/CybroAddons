# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo import fields


class TestMedicalLab(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMedicalLab, cls).setUpClass()

        # 1. Setup Patient partner
        cls.patient_partner = cls.env['res.partner'].create({
            'name': 'Test Patient',
            'is_patient': True,
            'phone': '9876543210',
            'email': 'patient@test.com',
        })

        # 2. Setup Physician speciality and partner
        cls.speciality = cls.env['physician.speciality'].create({
            'code': 'CARD',
            'name': 'Cardiology',
        })
        cls.physician_partner = cls.env['res.partner'].create({
            'name': 'Dr. Test Physician',
            'is_physician': True,
            'speciality_id': cls.speciality.id,
        })

        # 3. Setup Lab Patient
        cls.patient = cls.env['lab.patient'].create({
            'patient_id': cls.patient_partner.id,
            'dob': '2000-01-01',
            'gender': 'm',
            'phone': '9876543210',
            'email': 'patient@test.com',
        })

        # 4. Setup Test Unit & Content Type
        cls.unit = cls.env['test.unit'].create({
            'unit': 'mg/dL',
            'code': 'MGDL',
        })
        cls.content_type = cls.env['lab.test.content.type'].create({
            'content_type_name': 'Blood Sugar Content',
            'content_type_code': 'BSC',
        })

        # 5. Setup Lab Test and Attribute
        cls.lab_test = cls.env['lab.test'].create({
            'lab_test': 'Blood Sugar Test',
            'lab_test_code': 'BST',
            'test_cost': 150.0,
        })
        cls.test_attribute = cls.env['lab.test.attribute'].create({
            'test_content_id': cls.content_type.id,
            'unit_id': cls.unit.id,
            'interval': '70-100',
            'test_line_reverse_id': cls.lab_test.id,
        })

        # 6. Ensure standard sale journal exists for invoicing test
        cls.sale_journal = cls.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not cls.sale_journal:
            cls.account = cls.env['account.account'].search([('account_type', '=', 'income')], limit=1)
            if not cls.account:
                cls.account = cls.env['account.account'].create({
                    'name': 'Medical Lab Revenue',
                    'code': 'MLREV',
                    'account_type': 'income',
                })
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Lab Sales',
                'code': 'LABS',
                'type': 'sale',
                'default_account_id': cls.account.id,
            })

    def test_01_patient_management(self):
        """Test patient record creation, unique ID generation, and age computation."""
        # Check generated ID starts with PID
        self.assertTrue(self.patient.name.startswith('PID'))
        
        # Check age calculation
        # Patient was born 2000-01-01, date field default is current Datetime
        dob_dt = fields.Datetime.from_string(self.patient.dob)
        req_dt = fields.Datetime.from_string(self.patient.date)
        from dateutil.relativedelta import relativedelta
        delta = relativedelta(req_dt, dob_dt)
        expected_age = f"{delta.years} years"
        self.assertEqual(self.patient.age, expected_age)

    def test_02_lab_test_and_attributes(self):
        """Verify lab test attribute linking."""
        self.assertEqual(self.test_attribute.test_line_reverse_id, self.lab_test)
        self.assertIn(self.test_attribute, self.lab_test.test_lines_ids)

    def test_03_appointment_workflow(self):
        """Verify the full workflow of a lab appointment from draft, to confirmation, and to lab request."""
        # Create lab appointment
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'physician_id': self.physician_partner.id,
            'appointment_date': fields.Datetime.now(),
        })
        self.assertEqual(appointment.state, 'draft')

        # Add appointment line
        appointment_line = self.env['lab.appointment.lines'].create({
            'test_line_appointment_id': appointment.id,
            'lab_test_id': self.lab_test.id,
        })
        
        # Trigger cost onchange manually to simulate frontend selection
        appointment_line.cost_update()
        self.assertEqual(appointment_line.cost, 150.0)

        # Try requesting lab before confirming -> wait, code allows calling action_request in draft state?
        # Let's confirm the appointment first
        appointment.action_confirm_appointment()
        self.assertEqual(appointment.state, 'confirm')

        # Request lab tests
        appointment.action_request()
        self.assertEqual(appointment.state, 'request_lab')

        # Check that lab.request is generated
        requests = self.env['lab.request'].search([('app_id', '=', appointment.id)])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests.test_request_id, self.lab_test)
        self.assertEqual(len(requests.request_line_ids), 1)

    def test_04_lab_request_workflow(self):
        """Verify lab request state transitions and validation constraints."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'appointment_date': fields.Datetime.now(),
        })
        self.env['lab.appointment.lines'].create({
            'test_line_appointment_id': appointment.id,
            'lab_test_id': self.lab_test.id,
        })
        appointment.action_request()
        
        request = self.env['lab.request'].search([('app_id', '=', appointment.id)], limit=1)
        self.assertEqual(request.state, 'draft')

        # State transition 1: Sample Collection
        request.action_set_to_sample_collection()
        self.assertEqual(request.state, 'sample_collection')

        # State transition 2: Test in Progress
        request.action_set_to_test_in_progress()
        self.assertEqual(request.state, 'test_in_progress')

        # State transition 3: Complete Lab Request
        request.action_set_to_test_completed()
        self.assertEqual(request.state, 'completed')
        self.assertEqual(appointment.state, 'completed')

    def test_05_lab_request_validation(self):
        """Verify validation occurs when completing a request without attributes."""
        # Create request without request line attributes
        request = self.env['lab.request'].create({
            'lab_request_id': 'REQ_TEST_VALIDATION',
            'lab_requestor_id': self.patient.id,
            'lab_requesting_date': fields.Datetime.now(),
        })
        with self.assertRaises(ValidationError):
            request.action_set_to_test_completed()

    def test_06_invoice_workflow(self):
        """Test invoice creation, lines verification, and transition to invoiced state upon payment."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'appointment_date': fields.Datetime.now(),
        })
        self.env['lab.appointment.lines'].create({
            'test_line_appointment_id': appointment.id,
            'lab_test_id': self.lab_test.id,
            'cost': 150.0,
        })

        # Create invoice
        action = appointment.action_create_invoice()
        self.assertEqual(appointment.state, 'to_invoice')

        invoice_id = action.get('res_id')
        self.assertTrue(invoice_id)
        invoice = self.env['account.move'].browse(invoice_id)
        
        self.assertEqual(invoice.partner_id, self.patient_partner)
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.is_lab_invoice, True)
        self.assertEqual(invoice.lab_request_id, appointment)

        # Check invoice lines
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids[0].name, 'Blood Sugar Test')
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 150.0)

        # Simulate invoice payment
        invoice._invoice_paid_hook()
        self.assertEqual(appointment.state, 'invoiced')
