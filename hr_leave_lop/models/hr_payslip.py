# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fansa Jabeen A (odoo@cybrosys.com)
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
import logging
from odoo import models, fields
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    """
    HrPayslip model override to compute Loss of Pay based on adjacent holidays.
    """
    _inherit = 'hr.payslip'

    lop_amount = fields.Float(string='LOP Amount', default=0.0)


    def holiday(self, day):
        """
        Calculate the date of a specific weekly off day based on the payslip's start date.
        
        :param day: The day of the week as a string (0 for Monday, 6 for Sunday).
        :return: A list containing the string representation of the calculated holiday date.
        """
        if not self.date_from:
            return []
        current_date = self.date_from
        weekday = current_date.weekday()
        offset = (weekday - int(day)) % 7
        holiday_date = current_date - datetime.timedelta(days=offset)
        return [holiday_date.strftime('%Y-%m-%d')]

    def get_all_holidays(self):
        """
        Retrieve a list of weekly off dates for the employee relative to the payslip start date.
        
        :return: A list of string dates representing the weekly off days.
        """
        holidays = []
        all_days = ['0', '1', '2', '3', '4', '5', '6']
        calendar = self.employee_id.resource_calendar_id
        if not calendar:
            return holidays
        for attendance in calendar.attendance_ids:
            if attendance.dayofweek in all_days:
                all_days.remove(attendance.dayofweek)
        for day in all_days:
            holidays += self.holiday(day)
        return holidays

    def _is_public_holiday(self, check_date, public_holidays):
        """
        Check if a given date falls within any of the provided public holidays.
        
        :param check_date: The date to check (datetime or date object).
        :param public_holidays: Recordset of resource.calendar.leaves representing public holidays.
        :return: True if the date is a public holiday, False otherwise.
        """
        for holiday in public_holidays:
            start = fields.Datetime.context_timestamp(self, holiday.date_from).date()
            end = fields.Datetime.context_timestamp(self, holiday.date_to).date()
            if start <= check_date <= end:
                return True
        return False

    def compute_sheet(self):
        """
        Compute the payslip sheet. Overridden to first calculate and store the LOP amount.
        
        :return: Super call to compute_sheet.
        """
        for slip in self:
            slip._calculate_and_store_lop()
        return super().compute_sheet()


    def _calculate_and_store_lop(self):
        """
        Calculate the total Loss of Pay (LOP) amount based on leaves taken adjacent to holidays 
        or weekly off days, and store it in the lop_amount field. It also ensures the LOP 
        salary rule is created and added to the payslip structure.
        """
        self.ensure_one()

        # Get contract from employee's version_id (Odoo 19 structure)
        # Employee has version_id which contains wage information
        version = self.employee_id.version_id if self.employee_id and self.employee_id.version_id else None
        daily_wage = version.wage / 30 if version and version.wage else 0
        _logger.info(f"\n\n--- DEBUG LOP CALC for {self.employee_id.name} ---")
        _logger.info(f"Daily Wage: {daily_wage}")
        
        amount = 0
        all_days = ['0', '1', '2', '3', '4', '5', '6']
        calendar = self.employee_id.resource_calendar_id
        if calendar:
            for attendance in calendar.attendance_ids:
                if attendance.dayofweek in all_days:
                    all_days.remove(attendance.dayofweek)
        weekly_offs = all_days
        public_holidays = self.env['resource.calendar.leaves'].search([("resource_id", "=", False)])

        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', self.date_to),
            ('request_date_to', '>=', self.date_from)
        ])

        for leave in leaves:
            _logger.info(f"Checking Leave: {leave.request_date_from} to {leave.request_date_to}")
            no_of_days_before = 0
            no_of_days_after = 0
            prev_flag = next_flag = 0

            previous_date = leave.request_date_from - datetime.timedelta(days=1)
            next_date = leave.request_date_to + datetime.timedelta(days=1)

            temp_date = next_date
            while True:
                is_public = self._is_public_holiday(temp_date, public_holidays)
                is_weekly = str(temp_date.weekday()) in weekly_offs
                if not is_public and not is_weekly:
                    break
                if is_public:
                    no_of_days_after += 1
                    next_flag = 1  # Only public holidays determine the classification flag
                temp_date += datetime.timedelta(days=1)

            temp_date = previous_date
            while True:
                is_public = self._is_public_holiday(temp_date, public_holidays)
                is_weekly = str(temp_date.weekday()) in weekly_offs
                if not is_public and not is_weekly:
                    break
                if is_public:
                    no_of_days_before += 1
                    prev_flag = 1  # Only public holidays determine the classification flag
                temp_date -= datetime.timedelta(days=1)


            if next_flag and not prev_flag:
                leave_type = 'before_holiday'
                rule_days = no_of_days_after
            elif prev_flag and not next_flag:
                leave_type = 'after_holiday'
                rule_days = no_of_days_before
            elif next_flag and prev_flag:
                leave_type = 'between_holidays'
                rule_days = no_of_days_before + no_of_days_after
            else:
                leave_type = 'regular'
                rule_days = 0

            lop_rule = self.env['hr.leave.lop'].search([
                ('leave_type', '=', leave_type),
                ('no_of_days', '=', rule_days)
            ], limit=1)


            if lop_rule and lop_rule.deduction_amount > 0:
                lop_amount = lop_rule.no_of_days * daily_wage * (lop_rule.deduction_amount / 100)
            else:
                lop_amount = 0


            amount += lop_amount

        self.sudo().write({'lop_amount': amount})

        salary_rule = self.env['hr.salary.rule'].sudo().search([('code', '=', 'LOP')], limit=1)

        if not salary_rule:
            category = self.env['hr.salary.rule.category'].search([('code', '=', 'DED')], limit=1)
            if not category:
                category = self.env['hr.salary.rule.category'].search([], limit=1)
            salary_rule = self.env['hr.salary.rule'].sudo().create({
                'name': _('Loss of Pay'),
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