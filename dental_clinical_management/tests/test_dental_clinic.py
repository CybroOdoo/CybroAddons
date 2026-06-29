# -*- coding: utf-8 -*-
import json
from datetime import date
from unittest.mock import patch
from odoo.tests import HttpCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestDentalClinicController(HttpCase):
    """Test cases for the DentalClinic controller (dental_clinic.py)"""

    @classmethod
    def setUpClass(cls):
        super(TestDentalClinicController, cls).setUpClass()
        cls.specialist = cls.env['dental.specialist'].create({
            'name': 'Orthodontics',
        })
        cls.time_shift = cls.env['dental.time.shift'].create({
            'shift_type': 'morning',
            'start_time': 9.0,
            'end_time': 13.0,
        })
        cls.doctor = cls.env['hr.employee'].create({
            'name': 'Dr. Controller Test',
            'dob': date(1978, 5, 10),
            'specialised_in_id': cls.specialist.id,
            'time_shift_ids': [(4, cls.time_shift.id)],
        })
        cls.patient = cls.env['res.partner'].create({
            'name': 'Portal Patient',
        })

    def test_dental_clinic_page(self):
        """Test GET /dental_doctor returns 200 OK."""
        response = self.url_open('/dental_doctor')
        self.assertEqual(response.status_code, 200,
                         "The dental clinic page should return 200.")

    def test_success_appointment_page(self):
        """Test GET /success_appointment with required token query param returns 200."""
        # The template uses token['token'] so we must pass token as query param
        response = self.url_open('/success_appointment?token=1&appointment_id=1')
        self.assertEqual(response.status_code, 200,
                         "Success appointment page should return 200 when token is provided.")

    def test_all_doctors_page(self):
        """Test GET /all_doctors returns 200 OK."""
        response = self.url_open('/all_doctors')
        self.assertEqual(response.status_code, 200,
                         "All doctors page should return 200.")

    def test_get_patient_details(self):
        """Test /patient_details JSON-RPC endpoint returns patient data."""
        with patch('odoo.http.Request.validate_csrf', return_value=True):
            payload = json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 1,
                'params': {'patient_id': self.patient.id},
            })
            response = self.url_open(
                '/patient_details',
                data=payload.encode(),
                headers={'Content-Type': 'application/json'},
            )
        self.assertEqual(response.status_code, 200,
                         "get_patient_details should return 200.")

    def test_get_specialised_doctors(self):
        """Test /specialised_doctors JSON-RPC endpoint returns doctors by specialist."""
        with patch('odoo.http.Request.validate_csrf', return_value=True):
            payload = json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 2,
                'params': {'specialised_id': self.specialist.id},
            })
            response = self.url_open(
                '/specialised_doctors',
                data=payload.encode(),
                headers={'Content-Type': 'application/json'},
            )
        self.assertEqual(response.status_code, 200,
                         "get_specialised_doctors should return 200.")

    def test_get_doctors_shifts(self):
        """Test /doctors_shifts JSON-RPC endpoint returns shifts for a doctor."""
        with patch('odoo.http.Request.validate_csrf', return_value=True):
            payload = json.dumps({
                'jsonrpc': '2.0',
                'method': 'call',
                'id': 3,
                'params': {'doctor_id': self.doctor.id},
            })
            response = self.url_open(
                '/doctors_shifts',
                data=payload.encode(),
                headers={'Content-Type': 'application/json'},
            )
        self.assertEqual(response.status_code, 200,
                         "get_doctors_shifts should return 200.")
