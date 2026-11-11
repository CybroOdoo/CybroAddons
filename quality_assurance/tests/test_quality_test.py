# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies
#    (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged

from .common import QualityCommon


@tagged('post_install', '-at_install', 'quality_assurance')
class TestQualityTest(QualityCommon):

    def _create_test(self, measure):
        alert = self.env['quality.alert'].create({
            'name': 'Test Alert',
            'product_id': self.product.id,
        })
        return self.env['quality.test'].create({
            'quality_measure_id': measure.id,
            'alert_id': alert.id,
        })

    def test_related_fields(self):
        test = self._create_test(self.measure_qty)
        self.assertEqual(test.name, 'Weight Check')
        self.assertEqual(test.test_type, 'quantity')
        self.assertEqual(test.quantity_min, 5.0)
        self.assertEqual(test.quantity_max, 10.0)
        self.assertEqual(test.product_id, self.product)

    def test_quantitative_inside_range_passes(self):
        test = self._create_test(self.measure_qty)
        test.test_result = 7.5
        self.assertEqual(test.test_status, 'pass')

    def test_quantitative_boundaries_are_inclusive(self):
        test = self._create_test(self.measure_qty)
        test.test_result = 5.0
        self.assertEqual(test.test_status, 'pass')
        test.test_result = 10.0
        self.assertEqual(test.test_status, 'pass')

    def test_quantitative_outside_range_fails(self):
        test = self._create_test(self.measure_qty)
        test.test_result = 4.99
        self.assertEqual(test.test_status, 'fail')
        test.test_result = 10.01
        self.assertEqual(test.test_status, 'fail')

    def test_quantitative_default_result_fails(self):
        # Result defaults to 0.0, which is outside the 5-10 range.
        test = self._create_test(self.measure_qty)
        self.assertEqual(test.test_status, 'fail')

    def test_qualitative_satisfied_passes(self):
        test = self._create_test(self.measure_ql)
        test.test_result2 = 'satisfied'
        self.assertEqual(test.test_status, 'pass')

    def test_qualitative_unsatisfied_fails(self):
        test = self._create_test(self.measure_ql)
        test.test_result2 = 'unsatisfied'
        self.assertEqual(test.test_status, 'fail')

    def test_qualitative_without_result_fails(self):
        test = self._create_test(self.measure_ql)
        self.assertFalse(test.test_result2)
        self.assertEqual(test.test_status, 'fail')

    def test_status_recomputed_when_result_changes(self):
        test = self._create_test(self.measure_ql)
        test.test_result2 = 'satisfied'
        self.assertEqual(test.test_status, 'pass')
        test.test_result2 = 'unsatisfied'
        self.assertEqual(test.test_status, 'fail')

    def test_measure_deletion_cascades_to_tests(self):
        test = self._create_test(self.measure_qty)
        self.measure_qty.unlink()
        self.assertFalse(test.exists())
