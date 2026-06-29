# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests import TransactionCase, tagged
from odoo import fields
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestDentalDoctor(TransactionCase):
    """Test cases for DentalDoctor (hr.employee inheritance)"""

    @classmethod
    def setUpClass(cls):
        super(TestDentalDoctor, cls).setUpClass()
        cls.specialist = cls.env['dental.specialist'].create({
            'name': 'Orthodontics',
        })
        cls.time_shift = cls.env['dental.time.shift'].create({
            'shift_type': 'morning',
            'start_time': 9.0,
            'end_time': 13.0,
        })
        # Create a doctor without work_email to avoid user creation side effects
        cls.doctor = cls.env['hr.employee'].create({
            'name': 'Dr. Test',
            'specialised_in_id': cls.specialist.id,
            'dob': date(1980, 5, 20),
            'sex': 'male',
            'time_shift_ids': [(4, cls.time_shift.id)],
        })

    def test_create(self):
        """Test that create() successfully creates a doctor record."""
        self.assertTrue(self.doctor.exists(), "Doctor record should be created.")
        self.assertEqual(self.doctor.name, 'Dr. Test')

    def test_compute_doctor_age(self):
        """Test _compute_doctor_age correctly calculates age from dob."""
        self.doctor._compute_doctor_age()
        today = fields.Date.today()
        expected_age = (
            today.year - self.doctor.dob.year -
            ((today.month, today.day) < (self.doctor.dob.month, self.doctor.dob.day))
        )
        self.assertEqual(self.doctor.doctor_age, expected_age,
                         "Doctor age should be correctly computed from dob.")

    def test_check_dob_validation_future(self):
        """Test _check_dob_validation raises ValidationError for a future DOB."""
        with self.assertRaises(ValidationError):
            self.env['hr.employee'].create({
                'name': 'Future Doctor',
                'dob': date(2099, 1, 1),
            })

    def test_check_dob_validation_valid(self):
        """Test _check_dob_validation passes for a valid past DOB."""
        doctor = self.env['hr.employee'].create({
            'name': 'Dr. Valid',
            'dob': date(1975, 4, 10),
        })
        self.assertTrue(doctor.exists())

    def test_unlink(self):
        """Test unlink() deletes the doctor record."""
        doctor_to_delete = self.env['hr.employee'].create({
            'name': 'Dr. ToDelete',
            'dob': date(1970, 1, 1),
        })
        doctor_id = doctor_to_delete.id
        doctor_to_delete.unlink()
        self.assertFalse(self.env['hr.employee'].browse(doctor_id).exists(),
                         "Doctor record should be deleted.")
