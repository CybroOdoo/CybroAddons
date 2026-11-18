# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
import datetime
from types import SimpleNamespace
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.hr_payroll.tests.common import TestPayslipContractBase


@tagged('post_install', '-at_install')
class TestHrLeaveLop(TestPayslipContractBase):
    """Tests for LOP rules and their payslip calculation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.richard_emp
        cls.employee.resource_calendar_id = cls.calendar_35h
        cls.structure = cls.developer_pay_structure
        cls.wage = cls.employee.version_id.wage

    def _make_payslip(self, date_from='2026-01-01', date_to='2026-01-31'):
        return self.env['hr.payslip'].create({
            'name': 'LOP test payslip',
            'employee_id': self.employee.id,
            'version_id': self.employee.version_id.id,
            'struct_id': self.structure.id,
            'date_from': date_from,
            'date_to': date_to,
        })

    def _make_rule(self, leave_type, no_of_days, deduction_amount):
        return self.env['hr.leave.lop'].create({
            'name': '%s: %s day(s)' % (leave_type, no_of_days),
            'leave_type': leave_type,
            'no_of_days': no_of_days,
            'deduction_amount': deduction_amount,
        })

    def _fake_leave(self, date_from, date_to=None):
        date_from = datetime.date.fromisoformat(date_from)
        date_to = datetime.date.fromisoformat(date_to) if date_to else date_from
        return SimpleNamespace(
            request_date_from=date_from,
            request_date_to=date_to,
        )

    def _calculate_with_leaves(self, payslip, leaves, public_holiday_dates):
        public_holidays = {
            datetime.date.fromisoformat(day) for day in public_holiday_dates
        }
        leave_model = type(self.env['hr.leave'])
        payslip_model = type(payslip)
        with patch.object(leave_model, 'search', return_value=leaves), \
                patch.object(
                    payslip_model,
                    '_is_public_holiday',
                    side_effect=lambda check_date, holidays:
                    check_date in public_holidays,
                ):
            payslip._calculate_and_store_lop()

    def test_lop_rule_fields_and_copy_is_forbidden(self):
        rule = self._make_rule('before_holiday', 2, 25.0)

        self.assertEqual(rule.name, 'before_holiday: 2 day(s)')
        self.assertEqual(rule.leave_type, 'before_holiday')
        self.assertEqual(rule.no_of_days, 2)
        self.assertAlmostEqual(rule.deduction_amount, 25.0)
        with self.assertRaises(ValidationError):
            rule.copy()

    def test_holiday_returns_weekly_off_date_on_or_before_period_start(self):
        payslip = self._make_payslip('2026-01-05', '2026-01-31')  # Monday

        self.assertEqual(payslip.holiday('0'), ['2026-01-05'])
        self.assertEqual(payslip.holiday('6'), ['2026-01-04'])

        payslip_without_start = self.env['hr.payslip'].new({'date_from': False})
        self.assertEqual(payslip_without_start.holiday('6'), [])

    def test_get_all_holidays_uses_employee_calendar_days_off(self):
        payslip = self._make_payslip('2026-01-05', '2026-01-31')  # Monday

        self.assertCountEqual(
            payslip.get_all_holidays(), ['2026-01-04', '2026-01-03']
        )

        self.employee.resource_calendar_id = False
        self.assertEqual(payslip.get_all_holidays(), [])

    def test_calculation_covers_before_after_between_and_regular_leave(self):
        payslip = self._make_payslip()
        daily_wage = self.wage / 30
        self._make_rule('before_holiday', 1, 10)
        self._make_rule('after_holiday', 1, 20)
        self._make_rule('between_holidays', 2, 30)

        leaves = [
            self._fake_leave('2026-01-05'),  # Tuesday holiday follows: before
            self._fake_leave('2026-01-22'),  # Wednesday holiday precedes: after
            self._fake_leave('2026-01-27'),  # Monday and Wednesday: between
            self._fake_leave('2026-01-30'),  # No adjacent public holiday: regular
        ]
        self._calculate_with_leaves(
            payslip,
            leaves,
            ['2026-01-06', '2026-01-21', '2026-01-26', '2026-01-28'],
        )

        expected = daily_wage * (0.10 + 0.20 + 2 * 0.30)
        self.assertAlmostEqual(payslip.lop_amount, expected, places=2)
        lop_rule = self.env['hr.salary.rule'].search([('code', '=', 'LOP')], limit=1)
        self.assertTrue(lop_rule)
        self.assertIn(lop_rule, self.structure.rule_ids)
        self.assertEqual(lop_rule.amount_select, 'code')
        self.assertEqual(lop_rule.amount_python_compute, 'result = -payslip.lop_amount')

    def test_weekly_offs_are_skipped_but_only_public_holidays_count_for_rule(self):
        payslip = self._make_payslip()
        daily_wage = self.wage / 30
        self._make_rule('before_holiday', 1, 50)
        # Monday 2026-01-05 follows Sunday and a public holiday on Tuesday.
        self._calculate_with_leaves(
            payslip,
            [self._fake_leave('2026-01-05')],
            ['2026-01-06'],
        )

        self.assertAlmostEqual(payslip.lop_amount, daily_wage * 0.5, places=2)

    def test_zero_percent_or_missing_rule_produces_no_deduction(self):
        payslip = self._make_payslip()
        self._make_rule('before_holiday', 1, 0)
        self._calculate_with_leaves(
            payslip,
            [self._fake_leave('2026-01-05')],
            ['2026-01-06'],
        )
        self.assertEqual(payslip.lop_amount, 0)

        payslip.lop_amount = 0
        self._calculate_with_leaves(
            payslip,
            [self._fake_leave('2026-01-05')],
            ['2026-01-06', '2026-01-07'],  # No rule exists for two days.
        )
        self.assertEqual(payslip.lop_amount, 0)

    def test_no_matching_leave_resets_lop_amount_to_zero(self):
        payslip = self._make_payslip()
        payslip.lop_amount = 123.45

        self._calculate_with_leaves(payslip, [], [])

        self.assertEqual(payslip.lop_amount, 0)

