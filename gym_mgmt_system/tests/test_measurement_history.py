# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestMeasurementHistory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMeasurementHistory, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Measurement Member',
            'is_gym_member': True,
        })
        cls.measurement_male = cls.env['measurement.history'].create({
            'member_id': cls.partner.id,
            'gender': 'male',
            'age': 30,
            'weight': 80.0,
            'height': 180.0,
        })
        cls.measurement_female = cls.env['measurement.history'].create({
            'member_id': cls.partner.id,
            'gender': 'female',
            'age': 25,
            'weight': 60.0,
            'height': 165.0,
        })

    def test_bmi_bmr_calculation_male(self):
        """Test BMI and BMR calculations for male."""
        # BMI = (80 / 180 / 180) * 10000 = 24.691...
        self.assertAlmostEqual(self.measurement_male.bmi, 24.69, places=2)
        # BMR male = 66.47 + (13.75 * 80) + (5.003 * 180) - (6.755 * 30)
        # = 66.47 + 1100 + 900.54 - 202.65 = 1864.36
        self.assertAlmostEqual(self.measurement_male.bmr, 1864.36, places=2)

    def test_bmi_bmr_calculation_female(self):
        """Test BMI and BMR calculations for female."""
        # BMI = (60 / 165 / 165) * 10000 = 22.038...
        self.assertAlmostEqual(self.measurement_female.bmi, 22.04, places=2)
        # BMR female = 655.1 + (9.563 * 60) + (1.85 * 165) - (6.755 * 25)
        # = 655.1 + 573.78 + 305.25 - 168.875 = 1365.255
        self.assertAlmostEqual(self.measurement_female.bmr, 1365.255, places=2)
