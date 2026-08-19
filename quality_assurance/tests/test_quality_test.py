# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase

class TestQualityTest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({'name': 'Test Product QT'})
        cls.alert = cls.env['quality.alert'].create({'product_id': cls.product.id})

        cls.measure_quant = cls.env['quality.measure'].create({
            'name': 'Quant Measure',
            'type': 'quantity',
            'quantity_min': 5.0,
            'quantity_max': 10.0,
            'product_id': cls.product.id,
        })
        
        cls.measure_qual = cls.env['quality.measure'].create({
            'name': 'Qual Measure',
            'type': 'quality',
            'product_id': cls.product.id,
        })

    def test_01_compute_status_quantity(self):
        """Test _compute_quality_test_status for quantitative tests."""
        test = self.env['quality.test'].create({
            'quality_measure_id': self.measure_quant.id,
            'alert_id': self.alert.id,
        })
        
        # Test passing value
        test.test_result = 7.0
        test._compute_quality_test_status()
        self.assertEqual(test.test_status, 'pass', "Result within range should pass")
        
        # Test failing value
        test.test_result = 4.0
        test._compute_quality_test_status()
        self.assertEqual(test.test_status, 'fail', "Result out of range should fail")

    def test_02_compute_status_quality(self):
        """Test _compute_quality_test_status for qualitative tests."""
        test = self.env['quality.test'].create({
            'quality_measure_id': self.measure_qual.id,
            'alert_id': self.alert.id,
        })
        
        test.test_result2 = 'satisfied'
        test._compute_quality_test_status()
        self.assertEqual(test.test_status, 'pass', "'satisfied' should pass")
        
        test.test_result2 = 'unsatisfied'
        test._compute_quality_test_status()
        self.assertEqual(test.test_status, 'fail', "'unsatisfied' should fail")
