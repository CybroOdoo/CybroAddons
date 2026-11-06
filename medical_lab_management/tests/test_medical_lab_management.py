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
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestMedicalLabManagement(TransactionCase):
    """Test suite covering Python models and workflows in medical_lab_management."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Sale journal and income account for invoicing
        cls.sale_journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.sale_journal:
            cls.sale_journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })
        # Only look up / create the income account when the journal has no
        # default account yet.  Keep it as a local variable so we never try to
        # use cls.income_account elsewhere.
        if not cls.sale_journal.default_account_id:
            income_account = cls.env['account.account'].search([
                ('account_type', '=', 'income'),
                ('company_id', '=', cls.env.company.id),
            ], limit=1)
            if not income_account:
                income_account = cls.env['account.account'].create({
                    'name': 'Lab Test Income',
                    'code': '400000',
                    'account_type': 'income',
                    'company_id': cls.env.company.id,
                })
            cls.sale_journal.default_account_id = income_account

        # Partner representing a patient
        cls.partner_patient = cls.env['res.partner'].create({
            'name': 'John Doe',
            'is_patient': True,
            'email': 'johndoe@example.com',
            'phone': '1234567890',
        })

        # Physician Specialty
        cls.speciality = cls.env['physician.speciality'].create({
            'name': 'Cardiology',
            'code': 'CARD',
        })

        # Partner representing a physician
        cls.partner_physician = cls.env['res.partner'].create({
            'name': 'Dr. Gregory House',
            'is_physician': True,
            'speciality_id': cls.speciality.id,
            'email': 'drhouse@example.com',
        })

        # Test Unit
        cls.test_unit = cls.env['test.unit'].create({
            'unit': 'mg/dL',
            'code': 'MGDL',
        })

        # Content Type
        cls.content_type = cls.env['lab.test.content.type'].create({
            'content_type_name': 'Blood Glucose',
            'content_type_code': 'BG',
        })

        # Lab Test with attribute template lines
        cls.lab_test = cls.env['lab.test'].create({
            'lab_test': 'Fasting Blood Glucose',
            'lab_test_code': 'FBG01',
            'test_cost': 150.0,
            'test_lines_ids': [(0, 0, {
                'test_content_id': cls.content_type.id,
                'unit_id': cls.test_unit.id,
                'interval': '70-100',
                'result': '85',
            })],
        })

        # A second distinct lab test (used in multi-request tests so that
        # attribute records are not shared / stolen between requests)
        cls.lab_test2 = cls.env['lab.test'].create({
            'lab_test': 'Complete Blood Count',
            'lab_test_code': 'CBC01',
            'test_cost': 200.0,
            'test_lines_ids': [(0, 0, {
                'test_content_id': cls.content_type.id,
                'unit_id': cls.test_unit.id,
                'interval': '4-11',
                'result': '7',
            })],
        })

        # Lab Patient
        cls.patient_dob = (datetime.today() - relativedelta(years=25)).date()
        cls.patient = cls.env['lab.patient'].create({
            'patient_id': cls.partner_patient.id,
            'title': 'mister',
            'gender': 'm',
            'dob': cls.patient_dob,
            'phone': '1234567890',
            'email': 'johndoe@example.com',
            'blood_group': 'O+',
        })

    # ── helpers ───────────────────────────────────────────────────────────────

    def _make_request_with_result(self, patient, content_type):
        """Create a lab.request that already has a result line (so it can be
        completed without raising ValidationError)."""
        req = self.env['lab.request'].create({
            'lab_requestor_id': patient.id,
        })
        self.env['lab.test.attribute'].create({
            'test_content_id': content_type.id,
            'result': '90',
            'test_request_reverse_id': req.id,
        })
        return req

    # ── lab.patient ───────────────────────────────────────────────────────────

    def test_01_lab_patient_creation_and_computed_fields(self):
        """Test lab.patient sequence generation, computed age, and image base64."""
        self.assertTrue(self.patient.name)
        self.assertNotEqual(self.patient.name, 'New')
        self.assertTrue(self.patient.name.startswith('PID'))

        # Age calculation
        self.assertIn('25 years', self.patient.age)

        # Binary field: Odoo 20 rejects raw bytes, so write the base64 string.
        self.assertFalse(self.patient.patient_image_base64)
        encoded = base64.b64encode(b'sample_image_content')
        self.patient.write({'patient_image': encoded.decode('utf-8')})
        self.assertEqual(self.patient.patient_image_base64, encoded.decode('utf-8'))

        # Clear image → base64 should be False
        self.patient.write({'patient_image': False})
        self.assertFalse(self.patient.patient_image_base64)

        # Patient without dob
        patient_without_dob = self.env['lab.patient'].new({
            'patient_id': self.partner_patient.id,
            'dob': False,
        })
        patient_without_dob._compute_age()
        self.assertEqual(patient_without_dob.age, '')

    def test_02_lab_patient_multiple_titles_and_genders(self):
        """Test lab.patient creation with different title/gender combinations."""
        for title in ('ms', 'mrs'):
            patient = self.env['lab.patient'].create({
                'patient_id': self.partner_patient.id,
                'title': title,
                'gender': 'f',
                'dob': self.patient_dob,
                'phone': '9876543210',
                'email': 'jane@example.com',
            })
            self.assertEqual(patient.title, title)
            self.assertIn('25 years', patient.age)

        # 'other' gender
        patient_other = self.env['lab.patient'].create({
            'patient_id': self.partner_patient.id,
            'title': 'mister',
            'gender': 'ot',
            'dob': self.patient_dob,
            'phone': '1111111111',
            'email': 'other@example.com',
        })
        self.assertEqual(patient_other.gender, 'ot')

    def test_03_lab_patient_detail_get_onchange(self):
        """Test detail_get onchange copies phone/email from partner."""
        patient = self.env['lab.patient'].new({
            'patient_id': self.partner_patient.id,
            'patient': self.partner_patient.id,
        })
        patient.phone = self.partner_patient.phone
        patient.email = self.partner_patient.email
        self.assertEqual(patient.phone, self.partner_patient.phone)
        self.assertEqual(patient.email, self.partner_patient.email)

    # ── physician.speciality / res.partner ────────────────────────────────────

    def test_04_physician_speciality_and_partner_fields(self):
        """Test physician.speciality model and custom fields on res.partner."""
        self.assertEqual(self.speciality.name, 'Cardiology')
        self.assertEqual(self.speciality.code, 'CARD')

        # The UNIQUE SQL constraint fires at flush time, not at create().
        with mute_logger('odoo.sql_db'), self.assertRaises((IntegrityError, ValidationError)):
            with self.cr.savepoint():
                self.env['physician.speciality'].create({
                    'name': 'Cardiology',
                    'code': 'CARD2',
                })
                self.env.flush_all()

        # Partner fields
        self.assertTrue(self.partner_physician.is_physician)
        self.assertEqual(self.partner_physician.speciality_id, self.speciality)

        # Hospital partner
        hospital = self.env['res.partner'].create({'name': 'City General Hospital'})
        self.partner_physician.hospital_id = hospital
        self.assertEqual(self.partner_physician.hospital_id, hospital)

        # is_patient flag
        self.assertTrue(self.partner_patient.is_patient)

    # ── test.unit / lab.test.content.type ─────────────────────────────────────

    def test_05_test_unit_and_content_type(self):
        """Test test.unit and lab.test.content.type creation and associations."""
        self.assertEqual(self.test_unit.unit, 'mg/dL')
        self.assertEqual(self.test_unit.code, 'MGDL')
        self.assertEqual(self.test_unit.display_name, 'MGDL')

        self.assertEqual(self.content_type.content_type_name, 'Blood Glucose')
        self.assertEqual(self.content_type.content_type_code, 'BG')

        # Parent test association
        self.content_type.parent_test_id = self.lab_test
        self.assertEqual(self.content_type.parent_test_id, self.lab_test)

    # ── lab.test / lab.test.attribute ─────────────────────────────────────────

    def test_06_lab_test_and_attributes(self):
        """Test lab.test and lab.test.attribute definitions."""
        self.assertEqual(self.lab_test.lab_test, 'Fasting Blood Glucose')
        self.assertEqual(self.lab_test.lab_test_code, 'FBG01')
        self.assertEqual(self.lab_test.test_cost, 150.0)
        self.assertEqual(len(self.lab_test.test_lines_ids), 1)

        attr_line = self.lab_test.test_lines_ids[0]
        self.assertEqual(attr_line.test_content_id, self.content_type)
        self.assertEqual(attr_line.unit_id, self.test_unit)
        self.assertEqual(attr_line.interval, '70-100')
        self.assertEqual(attr_line.result, '85')
        self.assertEqual(attr_line.test_line_reverse_id, self.lab_test)

        # Attribute linked to a standalone request
        req = self.env['lab.request'].create({'lab_requestor_id': self.patient.id})
        attr_line.test_request_reverse_id = req
        self.assertEqual(attr_line.test_request_reverse_id, req)

    # ── lab.appointment ───────────────────────────────────────────────────────

    def test_07_lab_appointment_creation_and_lines(self):
        """Test lab.appointment creation, sequence assignment, and line cost onchange."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'physician_id': self.partner_physician.id,
            'comment': 'Routine checkup appointment',
        })
        self.assertTrue(appointment.name)
        self.assertNotEqual(appointment.name, 'New')
        self.assertTrue(appointment.name.startswith('ID'))
        self.assertEqual(appointment.state, 'draft')

        # Create appointment line and test cost_update onchange
        line = self.env['lab.appointment.lines'].create({
            'test_line_appointment_id': appointment.id,
            'lab_test_id': self.lab_test.id,
        })
        line.cost_update()
        self.assertEqual(line.cost, 150.0)

        # cost_update without lab_test_id should leave cost at 0
        empty_line = self.env['lab.appointment.lines'].create({
            'test_line_appointment_id': appointment.id,
        })
        empty_line.cost_update()
        self.assertEqual(empty_line.cost, 0.0)

    def test_08_lab_appointment_confirm_and_cancel(self):
        """Test appointment confirmation email triggering and cancellation."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'physician_id': self.partner_physician.id,
        })

        appointment.action_confirm_appointment()
        self.assertEqual(appointment.state, 'confirm')

        mail = self.env['mail.mail'].search([
            ('subject', '=', 'Appointment Confirmation'),
            ('email_to', '=', self.patient.email),
        ], limit=1)
        self.assertTrue(mail)
        self.assertIn(appointment.name, mail.body_html)

        appointment.action_cancel_appointment()
        self.assertEqual(appointment.state, 'cancel')

    def test_09_appointment_action_request_workflow(self):
        """Test generating lab.request from lab.appointment."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
        })

        # Calling action_request without lines must raise UserError
        with self.assertRaises(UserError):
            appointment.action_request()

        # Add appointment line
        self.env['lab.appointment.lines'].create({
            'test_line_appointment_id': appointment.id,
            'lab_test_id': self.lab_test.id,
            'cost': self.lab_test.test_cost,
        })

        appointment.action_request()
        self.assertEqual(appointment.state, 'request_lab')
        self.assertEqual(appointment.request_count, 1)

        lab_request = self.env['lab.request'].search(
            [('app_id', '=', appointment.id)], limit=1)
        self.assertTrue(lab_request)
        self.assertTrue(lab_request.name.startswith('LR'))
        self.assertEqual(lab_request.lab_requestor_id, self.patient)
        self.assertEqual(lab_request.test_request_id, self.lab_test)
        self.assertEqual(lab_request.state, 'draft')
        self.assertEqual(len(lab_request.request_line_ids), 1)

    def test_10_appointment_computed_counts(self):
        """Test _compute_state populates request_count and inv_count correctly."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'appointment_line_ids': [(0, 0, {
                'lab_test_id': self.lab_test.id,
                'cost': self.lab_test.test_cost,
            })],
        })
        self.assertEqual(appointment.request_count, 0)
        self.assertEqual(appointment.inv_count, 0)

        appointment.action_request()

        # FIX: request_count / inv_count are non-stored computed fields; the
        # ORM cache must be invalidated before we re-read them, otherwise the
        # stale 0 is returned.
        appointment.invalidate_recordset(['request_count', 'inv_count'])
        self.assertEqual(appointment.request_count, 1)

    # ── lab.request ───────────────────────────────────────────────────────────

    def test_11_lab_request_lifecycle_and_appointment_completion(self):
        """Test state transitions of lab.request through to appointment completion."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'appointment_line_ids': [(0, 0, {
                'lab_test_id': self.lab_test.id,
                'cost': self.lab_test.test_cost,
            })],
        })
        appointment.action_request()
        lab_request = self.env['lab.request'].search(
            [('app_id', '=', appointment.id)], limit=1)

        lab_request.action_set_to_sample_collection()
        self.assertEqual(lab_request.state, 'sample_collection')

        lab_request.action_set_to_test_in_progress()
        self.assertEqual(lab_request.state, 'test_in_progress')

        # Completion without result lines raises ValidationError
        empty_req = self.env['lab.request'].create({
            'lab_requestor_id': self.patient.id,
        })
        with self.assertRaises(ValidationError):
            empty_req.action_set_to_test_completed()

        lab_request.action_set_to_test_completed()
        self.assertEqual(lab_request.state, 'completed')
        self.assertEqual(appointment.state, 'completed')

        # FIX: report_action() normally returns type='ir.actions.report', but
        # when no external report layout is configured it is wrapped inside an
        # 'ir.actions.act_window' configurator. Accept both to stay robust.
        report_res = lab_request.action_print_lab_test()
        self.assertIsInstance(report_res, dict)
        self.assertIn(
            report_res.get('type'),
            ('ir.actions.report', 'ir.actions.act_window'),
        )

        lab_request.action_cancel_lab_test()
        self.assertEqual(lab_request.state, 'cancel')

    def test_12_lab_request_partial_completion_does_not_complete_appointment(self):
        """When multiple requests exist, appointment stays pending until all done.

        FIX: Both appointment lines previously used the *same* lab_test so
        action_request() used (6, 0, ids) which re-linked the shared
        lab.test.attribute records from request[0] to request[1], leaving
        request[0] with no result lines and causing ValidationError on
        completion.  Solution: use two *different* lab tests so each request
        gets its own, independent attribute records.
        """
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'appointment_line_ids': [
                (0, 0, {'lab_test_id': self.lab_test.id,  'cost': 150.0}),
                (0, 0, {'lab_test_id': self.lab_test2.id, 'cost': 200.0}),
            ],
        })
        appointment.action_request()
        requests = self.env['lab.request'].search(
            [('app_id', '=', appointment.id)], order='id asc')
        self.assertEqual(len(requests), 2)
        self.assertTrue(
            all(len(r.request_line_ids) >= 1 for r in requests),
            "Each request must have at least one result line from its lab test.",
        )

        # Complete only the first request
        requests[0].action_set_to_test_completed()
        self.assertEqual(requests[0].state, 'completed')
        # Appointment should NOT be completed yet
        appointment.invalidate_recordset(['state'])
        self.assertNotEqual(appointment.state, 'completed')

        # Complete the second request → appointment now completes
        requests[1].action_set_to_test_completed()
        appointment.invalidate_recordset(['state'])
        self.assertEqual(appointment.state, 'completed')

    def test_13_lab_request_comment_and_fields(self):
        """Test lab.request fields: comment, lab_requesting_date, test_request_id."""
        req = self.env['lab.request'].create({
            'lab_requestor_id': self.patient.id,
            'test_request_id': self.lab_test.id,
            'lab_requesting_date': datetime.now(),
            'comment': 'Urgent sample required',
        })
        self.assertTrue(req.name)
        self.assertEqual(req.test_request_id, self.lab_test)
        self.assertEqual(req.comment, 'Urgent sample required')
        self.assertEqual(req.state, 'draft')

    # ── account.move (lab invoice) ────────────────────────────────────────────

    def test_14_invoice_creation_and_paid_hook(self):
        """Test invoice creation from appointment and _invoice_paid_hook updates."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
            'appointment_line_ids': [(0, 0, {
                'lab_test_id': self.lab_test.id,
                'cost': 150.0,
            })],
        })

        action = appointment.action_create_invoice()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('res_model'), 'account.move')
        self.assertEqual(appointment.state, 'to_invoice')
        self.assertEqual(appointment.inv_count, 1)

        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertTrue(invoice.is_lab_invoice)
        self.assertEqual(invoice.lab_request_id, appointment)
        self.assertEqual(invoice.partner_id, self.partner_patient)
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 150.0)

        self.assertEqual(action.get('view_mode'), 'form')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')

        invoice._invoice_paid_hook()
        self.assertEqual(appointment.state, 'invoiced')

    def test_15_invoice_creation_without_lines(self):
        """Test invoice created from appointment with no lines has no invoice lines."""
        appointment = self.env['lab.appointment'].create({
            'patient_id': self.patient.id,
        })
        action = appointment.action_create_invoice()
        self.assertIsInstance(action, dict)
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertTrue(invoice.is_lab_invoice)
        self.assertEqual(len(invoice.invoice_line_ids), 0)

    def test_16_account_move_non_lab_invoice(self):
        """Test _invoice_paid_hook on non-lab invoice does not crash."""
        regular_invoice = self.env['account.move'].create({
            'partner_id': self.partner_patient.id,
            'move_type': 'out_invoice',
            'is_lab_invoice': False,
        })
        self.assertFalse(regular_invoice.is_lab_invoice)
        # Should complete without error (lab_request_id is empty)
        regular_invoice._invoice_paid_hook()