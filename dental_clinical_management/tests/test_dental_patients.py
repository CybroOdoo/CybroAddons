# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests import TransactionCase, tagged
from odoo import fields
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestDentalPatients(TransactionCase):
    """Test cases for DentalPatients (res.partner inheritance)"""

    @classmethod
    def setUpClass(cls):
        super(TestDentalPatients, cls).setUpClass()
        cls.patient = cls.env['res.partner'].create({
            'name': 'Test Patient',
            'dob': date(1990, 6, 15),
        })

    def test_create(self):
        """Test that create() sets company_type='person' and is_patient=True."""
        self.assertEqual(self.patient.company_type, 'person',
                         "company_type should be set to 'person' on create.")
        self.assertTrue(self.patient.is_patient,
                        "is_patient should be True on create.")

    def test_compute_patient_age(self):
        """Test _compute_patient_age correctly calculates age from dob."""
        self.patient._compute_patient_age()
        today = fields.Date.today()
        expected_age = (
            today.year - self.patient.dob.year -
            ((today.month, today.day) < (self.patient.dob.month, self.patient.dob.day))
        )
        self.assertEqual(self.patient.patient_age, expected_age,
                         "Patient age should be calculated correctly.")

    def test_check_dob_validation_future_date(self):
        """Test _check_dob_validation raises ValidationError for future DOB."""
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                'name': 'Future Patient',
                'dob': date(2099, 1, 1),
            })

    def test_check_dob_validation_valid_date(self):
        """Test _check_dob_validation passes for a valid past DOB."""
        patient = self.env['res.partner'].create({
            'name': 'Valid Patient',
            'dob': date(1985, 3, 10),
        })
        self.assertTrue(patient.exists())
