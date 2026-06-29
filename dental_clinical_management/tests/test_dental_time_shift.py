# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDentalTimeShift(TransactionCase):
    """Test cases for dental.time.shift model"""

    @classmethod
    def setUpClass(cls):
        super(TestDentalTimeShift, cls).setUpClass()
        cls.time_shift = cls.env['dental.time.shift'].create({
            'shift_type': 'morning',
            'start_time': 9.0,
            'end_time': 13.0,
        })

    def test_create(self):
        """Test that create() correctly sets name as 'start_time to end_time'."""
        self.assertEqual(
            self.time_shift.name,
            '9.0 to 13.0',
            "Name should be formatted as 'start_time to end_time' after create."
        )

    def test_onchange_time(self):
        """Test _onchange_time updates the name field dynamically."""
        shift = self.env['dental.time.shift'].new({
            'shift_type': 'evening',
            'start_time': 17.0,
            'end_time': 21.0,
        })
        shift._onchange_time()
        self.assertEqual(
            shift.name,
            '17.0 to 21.0',
            "Onchange should update name to 'start_time to end_time'."
        )
