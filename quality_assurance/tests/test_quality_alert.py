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
from odoo import Command
from odoo.tests import tagged

from .common import QualityCommon


@tagged('post_install', '-at_install', 'quality_assurance')
class TestQualityAlert(QualityCommon):

    def setUp(self):
        super().setUp()
        self.picking = self._create_picking()
        self.alert = self.env['quality.alert'].create({
            'name': 'Alert',
            'product_id': self.product.id,
            'picking_id': self.picking.id,
        })

    def test_defaults(self):
        self.assertTrue(self.alert.date)
        self.assertEqual(self.alert.user_id, self.env.user)
        self.assertEqual(self.alert.company_id, self.env.company)

    def test_sequence_generates_unique_names(self):
        seq = self.env['ir.sequence']
        first = seq.next_by_code('quality.alert')
        second = seq.next_by_code('quality.alert')
        self.assertTrue(first.startswith('QA'))
        self.assertNotEqual(first, second)

    def test_final_status_wait_without_tests(self):
        self.assertFalse(self.alert.tests)
        self.assertEqual(self.alert.final_status, 'wait')

    def test_final_status_pass_when_all_tests_pass(self):
        self.alert.action_generate_tests()
        self._fill_tests(self.alert)
        self.assertEqual(self.alert.final_status, 'pass')

    def test_final_status_fail_when_any_test_fails(self):
        self.alert.action_generate_tests()
        self._fill_tests(self.alert, qty_result=99.0)
        self.assertEqual(self.alert.final_status, 'fail')

    def test_final_status_follows_test_changes(self):
        self.alert.action_generate_tests()
        self._fill_tests(self.alert, ql_result='unsatisfied')
        self.assertEqual(self.alert.final_status, 'fail')
        self._fill_tests(self.alert, ql_result='satisfied')
        self.assertEqual(self.alert.final_status, 'pass')

    def test_final_status_wait_after_tests_removed(self):
        self.alert.action_generate_tests()
        self.alert.tests.unlink()
        self.assertEqual(self.alert.final_status, 'wait')

    def test_generate_tests_creates_one_test_per_measure(self):
        self.alert.action_generate_tests()
        self.assertEqual(len(self.alert.tests), 2)
        self.assertEqual(self.alert.tests.quality_measure_id,
                         self.measure_qty | self.measure_ql)

    def test_generate_tests_ignores_other_picking_types(self):
        other = self.env['quality.measure'].create({
            'name': 'Outgoing Only',
            'product_id': self.product.id,
            'picking_type_ids': [Command.set(self.out_type.ids)],
        })
        self.alert.action_generate_tests()
        self.assertNotIn(other, self.alert.tests.quality_measure_id)

    def test_generate_tests_ignores_other_products(self):
        other = self.env['quality.measure'].create({
            'name': 'Other Product',
            'product_id': self.product_plain.id,
            'picking_type_ids': [Command.set(self.in_type.ids)],
        })
        self.alert.action_generate_tests()
        self.assertNotIn(other, self.alert.tests.quality_measure_id)

    def test_generate_tests_ignores_archived_measures(self):
        self.measure_ql.toggle_active()
        self.alert.action_generate_tests()
        self.assertEqual(self.alert.tests.quality_measure_id,
                         self.measure_qty)

    def test_generate_tests_without_matching_measures(self):
        alert = self.env['quality.alert'].create({
            'name': 'Plain Alert',
            'product_id': self.product_plain.id,
            'picking_id': self.picking.id,
        })
        alert.action_generate_tests()
        self.assertFalse(alert.tests)
        self.assertEqual(alert.final_status, 'wait')
