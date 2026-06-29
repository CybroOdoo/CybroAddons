# -*- coding: utf-8 -*-
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDentalPrescriptionLines(TransactionCase):
    """Test cases for dental.prescription_lines model"""

    @classmethod
    def setUpClass(cls):
        super(TestDentalPrescriptionLines, cls).setUpClass()
        # medicine.frequency uses 'medicament_frequency' as _rec_name, not 'name'
        cls.frequency = cls.env['medicine.frequency'].create({
            'medicament_frequency': 'Once a day',
        })
        cls.medicine_product = cls.env['product.template'].create({
            'name': 'Amoxicillin',
            'is_medicine': True,
            'list_price': 10.0,
        })
        cls.prescription_line = cls.env['dental.prescription_lines'].new({
            'medicament_id': cls.medicine_product.id,
            'medicament_form': 'tablet',
            'quantity': 3,
            'frequency_id': cls.frequency.id,
        })

    def test_onchange_quantity(self):
        """Test _onchange_quantity updates total = price * quantity."""
        self.prescription_line._onchange_quantity()
        expected_total = self.prescription_line.price * self.prescription_line.quantity
        self.assertAlmostEqual(
            self.prescription_line.total,
            expected_total,
            msg="Total should be price × quantity after onchange."
        )
