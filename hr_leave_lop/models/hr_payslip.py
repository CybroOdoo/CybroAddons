# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Fansa Jabeen A (odoo@cybrosys.com)
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
from odoo import models, fields

class HrPayslip(models.Model):
    """Extend hr.payslip to compute and store Loss of Pay (LOP) deductions."""
    _inherit = 'hr.payslip'

    lop_amount = fields.Float(string='LOP Amount', default=0.0)

    def get_all_weekly_offs(self):
        """Return a set of all weekly off dates within the payslip period."""
        weekly_off_dates = set()
        if not self.date_from or not self.date_to:
            return weekly_off_dates

        calendar = self.employee_id.resource_calendar_id
        if not calendar:
            return weekly_off_dates

        # Find which weekdays are working days (0=Mon ... 6=Sun)
        working_weekdays = set()
        for attendance in calendar.attendance_ids:
            working_weekdays.add(int(attendance.dayofweek))

        # Collect all off-weekday dates in a wide range around the payslip
        # (include buffer before/after to catch adjacent-holiday checks)
        start = self.date_from - datetime.timedelta(days=7)
        end = self.date_to + datetime.timedelta(days=7)
        current = start
        while current <= end:
            if current.weekday() not in working_weekdays:
                weekly_off_dates.add(current)
            current += datetime.timedelta(days=1)

        return weekly_off_dates

    def _is_public_holiday(self, check_date, public_holidays):
        """Check whether a given date falls within a public holiday period."""
        for holiday in public_holidays:
            # date_from / date_to are datetime fields on resource.calendar.leaves
            start = holiday.date_from.date() if hasattr(holiday.date_from, 'date') else holiday.date_from
            end = holiday.date_to.date() if hasattr(holiday.date_to, 'date') else holiday.date_to
            if start <= check_date <= end:
                return True
        return False

    def _is_off_day(self, check_date, public_holidays, weekly_offs):
        """Return True if check_date is a public holiday or weekly off."""
        return self._is_public_holiday(check_date, public_holidays) or check_date in weekly_offs

    def compute_sheet(self):
        """Override compute_sheet to calculate LOP before computing payslip."""
        for slip in self:
            slip._calculate_and_store_lop()
        return super().compute_sheet()

    def _calculate_and_store_lop(self):
        """Calculate Loss of Pay based on leave rules and store it in the payslip."""
        self.ensure_one()

        daily_wage = self.contract_id.wage / 30.0 if self.contract_id else 0
        amount = 0

        # FIX: use corrected weekly-offs method that returns actual date objects
        weekly_offs = self.get_all_weekly_offs()

        public_holidays = self.env['resource.calendar.leaves'].search(
            [("resource_id", "=", False)])

        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', self.date_to),
            ('request_date_to', '>=', self.date_from)
        ])

        for leave in leaves:
            no_of_days_before = 0
            no_of_days_after = 0
            prev_flag = next_flag = 0

            # Check days BEFORE the leave start
            temp_date = leave.request_date_from - datetime.timedelta(days=1)
            while self._is_off_day(temp_date, public_holidays, weekly_offs):
                no_of_days_before += 1
                prev_flag = 1
                temp_date -= datetime.timedelta(days=1)

            # Check days AFTER the leave end
            temp_date = leave.request_date_to + datetime.timedelta(days=1)
            while self._is_off_day(temp_date, public_holidays, weekly_offs):
                no_of_days_after += 1
                next_flag = 1
                temp_date += datetime.timedelta(days=1)

            # FIX: corrected leave_type logic
            # prev_flag=1 means there's a holiday BEFORE the leave → leave is AFTER a holiday
            # next_flag=1 means there's a holiday AFTER the leave → leave is BEFORE a holiday
            if next_flag and prev_flag:
                leave_type = 'between_holidays'
                rule_days = no_of_days_before + no_of_days_after
            elif next_flag and not prev_flag:
                leave_type = 'before_holiday'   # leave day is just before a holiday
                rule_days = no_of_days_after
            elif prev_flag and not next_flag:
                leave_type = 'after_holiday'    # leave day is just after a holiday
                rule_days = no_of_days_before
            else:
                leave_type = 'regular'
                rule_days = 0

            if leave_type == 'regular':
                continue

            if leave_type == 'between_holidays':
                lop_rule = self.env['hr.leave.lop'].search([
                    ('leave_type', '=', leave_type),
                    ('no_of_days_before', '<=', no_of_days_before),
                    ('no_of_days_after', '<=', no_of_days_after)
                ], limit=1, order='no_of_days_before desc, no_of_days_after desc')
            else:
                lop_rule = self.env['hr.leave.lop'].search([
                    ('leave_type', '=', leave_type),
                    ('no_of_days', '<=', rule_days)
                ], limit=1, order='no_of_days desc')


            if lop_rule and lop_rule.deduction_amount > 0:
                lop_amount = daily_wage * (lop_rule.deduction_amount / 100)
            else:
                lop_amount = 0

            amount += lop_amount

        self.sudo().write({'lop_amount': amount})

        salary_rule = self.env['hr.salary.rule'].sudo().search(
            [('code', '=', 'LOP')], limit=1)

        if not salary_rule:
            category = self.env['hr.salary.rule.category'].search(
                [('code', '=', 'DED')], limit=1)
            if not category:
                category = self.env['hr.salary.rule.category'].search([], limit=1)
            salary_rule = self.env['hr.salary.rule'].sudo().create({
                'name': 'Loss of Pay',
                'code': 'LOP',
                'sequence': 999,
                'category_id': category.id,
                'struct_id': self.struct_id.id,
                'active': True,
                'appears_on_payslip': True,
                'condition_select': 'none',
                'amount_select': 'code',
                'amount_python_compute': 'result = -payslip.lop_amount',
            })
        else:
            if salary_rule.amount_select != 'code':
                salary_rule.sudo().write({
                    'amount_select': 'code',
                    'amount_python_compute': 'result = -payslip.lop_amount',
                })

        if salary_rule.id not in self.struct_id.rule_ids.ids:
            self.struct_id.sudo().write({'rule_ids': [(4, salary_rule.id)]})
