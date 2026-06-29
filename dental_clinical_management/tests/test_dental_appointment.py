# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests import TransactionCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestDentalAppointment(TransactionCase):
    """Test cases for dental.appointment model"""

    @classmethod
    def setUpClass(cls):
        super(TestDentalAppointment, cls).setUpClass()
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
        cls.appointment = cls.env['dental.appointment'].create({
            'patient_id': cls.patient.id,
            'specialist_id': cls.specialist.id,
            'doctor_id': cls.doctor.id,
            'shift_id': cls.time_shift.id,
            'date': fields.Date.today(),
        })

    def test_create(self):
        """Test create() generates a sequence number and sets state to 'new'."""
        self.assertTrue(self.appointment.sequence_no,
                        "Sequence number should be assigned on create.")
        self.assertNotEqual(self.appointment.sequence_no, 'New',
                            "Sequence number should not remain 'New' after create.")
        self.assertEqual(self.appointment.state, 'new',
                         "State should be set to 'new' on create.")

    def test_create_token_no(self):
        """Test that token_no is assigned incrementally for same doctor/date/shift."""
        appointment2 = self.env['dental.appointment'].create({
            'patient_id': self.patient.id,
            'specialist_id': self.specialist.id,
            'doctor_id': self.doctor.id,
            'shift_id': self.time_shift.id,
            'date': fields.Date.today(),
        })
        self.assertGreater(appointment2.token_no, self.appointment.token_no,
                           "Second appointment token should be greater than first.")

    def test_onchange_specialist_id(self):
        """Test _onchange_specialist_id clears the doctor field."""
        appt = self.env['dental.appointment'].new({
            'patient_id': self.patient.id,
            'specialist_id': self.specialist.id,
            'doctor_id': self.doctor.id,
        })
        appt._onchange_specialist_id()
        self.assertFalse(appt.doctor_id,
                         "doctor_id should be cleared when specialist changes.")

    def test_onchange_doctor_id(self):
        """Test _onchange_doctor_id clears the shift field."""
        appt = self.env['dental.appointment'].new({
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'shift_id': self.time_shift.id,
        })
        appt._onchange_doctor_id()
        self.assertFalse(appt.shift_id,
                         "shift_id should be cleared when doctor changes.")

    def test_compute_time_shifts(self):
        """Test _compute_time_shifts returns doctor's assigned shifts."""
        self.appointment._compute_time_shifts()
        self.assertIn(self.time_shift, self.appointment.time_shift_ids,
                      "Doctor's shift should appear in computed time_shift_ids.")

    def test_compute_doctor_ids(self):
        """Test _compute_doctor_ids returns doctors matching the specialist."""
        self.appointment._compute_doctor_ids()
        self.assertIn(self.doctor, self.appointment.doctor_ids,
                      "Doctor with matching specialist should appear in doctor_ids.")

    def test_action_cancel(self):
        """Test action_cancel sets state to 'cancel'."""
        self.appointment.action_cancel()
        self.assertEqual(self.appointment.state, 'cancel',
                         "State should be 'cancel' after action_cancel.")

    def test_action_create_appointment(self):
        """Test action_create_appointment sets state to 'new'."""
        self.appointment.action_cancel()
        self.appointment.action_create_appointment()
        self.assertEqual(self.appointment.state, 'new',
                         "State should be 'new' after action_create_appointment.")

    def test_action_prescription(self):
        """Test action_prescription returns correct action window."""
        action = self.appointment.action_prescription()
        self.assertEqual(action['res_model'], 'dental.prescription',
                         "res_model should be 'dental.prescription'.")
        self.assertIn(('appointment_id', '=', self.appointment.id), action['domain'],
                      "Domain should filter by appointment_id.")
        self.assertEqual(action['context']['default_patient_id'], self.patient.id)
