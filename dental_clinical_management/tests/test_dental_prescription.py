# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests import TransactionCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestDentalPrescription(TransactionCase):
    """Test cases for dental.prescription model"""

    @classmethod
    def setUpClass(cls):
        super(TestDentalPrescription, cls).setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Test Patient',
        })
        cls.specialist = cls.env['dental.specialist'].create({
            'name': 'General Dentistry',
        })
        cls.time_shift = cls.env['dental.time.shift'].create({
            'shift_type': 'morning',
            'start_time': 9.0,
            'end_time': 13.0,
        })
        cls.doctor = cls.env['hr.employee'].create({
            'name': 'Dr. Test',
            'dob': date(1975, 1, 1),
            'specialised_in_id': cls.specialist.id,
            'time_shift_ids': [(4, cls.time_shift.id)],
        })
        cls.treatment = cls.env['dental.treatment'].create({
            'name': 'Root Canal',
            'cost': 500.0,
        })
        cls.appointment = cls.env['dental.appointment'].create({
            'patient_id': cls.patient.id,
            'specialist_id': cls.specialist.id,
            'doctor_id': cls.doctor.id,
            'shift_id': cls.time_shift.id,
            'date': fields.Date.today(),
            'state': 'new',
        })
        cls.prescription = cls.env['dental.prescription'].create({
            'appointment_id': cls.appointment.id,
            'treatment_id': cls.treatment.id,
        })

    def test_create(self):
        """Test create() assigns a sequence number to the prescription."""
        self.assertTrue(self.prescription.sequence_no,
                        "Sequence number should be assigned on create.")
        self.assertNotEqual(self.prescription.sequence_no, 'New',
                            "Sequence number should not remain 'New'.")

    def test_compute_appointment_ids(self):
        """Test _compute_appointment_ids populates appointment_ids with today's new appointments."""
        self.prescription._compute_appointment_ids()
        self.assertIn(self.appointment, self.prescription.appointment_ids,
                      "Today's 'new' appointments should appear in appointment_ids.")

    def test_action_prescribed(self):
        """Test action_prescribed sets prescription and appointment state to 'done'."""
        self.prescription.action_prescribed()
        self.assertEqual(self.prescription.state, 'done',
                         "Prescription state should be 'done'.")
        self.assertEqual(self.appointment.state, 'done',
                         "Appointment state should be 'done' after prescribing.")

    def test_compute_grand_total(self):
        """Test _compute_grand_total sums treatment cost and medicine totals."""
        self.prescription._compute_grand_total()
        # With no medicine lines, grand_total = treatment cost
        self.assertAlmostEqual(self.prescription.grand_total, self.treatment.cost,
                               msg="Grand total should equal treatment cost when no medicines.")

    def test_action_view_invoice(self):
        """Test action_view_invoice returns correct action dict."""
        # Create a mock invoice to link
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.patient.id,
        })
        self.prescription.invoice_data_id = invoice.id
        action = self.prescription.action_view_invoice()
        self.assertEqual(action['res_model'], 'account.move',
                         "res_model should be 'account.move'.")
        self.assertEqual(action['res_id'], invoice.id,
                         "res_id should match the linked invoice ID.")

    def test_create_invoice(self):
        """Test create_invoice creates an invoice and sets state to 'invoiced'."""
        self.prescription.create_invoice()
        self.assertEqual(self.prescription.state, 'invoiced',
                         "Prescription state should be 'invoiced' after creating invoice.")
        self.assertTrue(self.prescription.invoice_data_id,
                        "invoice_data_id should be set after create_invoice.")
