# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Noorjahan N A (odoo@cybrosys.com)
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
from pandas import date_range
from odoo import api, models
from odoo.tools import date_utils


class HrPayslip(models.Model):
    """ Extended model for HR Payslip"""
    _inherit = 'hr.payslip'

    def holiday(self, day):
        """Get a list of dates for a given frequency.
        Args:
            day (str): Frequency of the dates (e.g., 'W-MON' for Mondays).
        Returns:
            list: List of dates in '%Y-%m-%d' format.
        """
        return date_range(
            start=str(date_utils.start_of(
                self.date_from.replace(month=self.date_from.month - 1),
                'month')),
            end=str(date_utils.end_of(
                self.date_from.replace(month=self.date_from.month + 1),
                'month')),
            freq=day).strftime(
            '%Y-%m-%d').tolist()

    def get_all_holidays(self):
        """Get all holidays based on the employee's working days.
        Returns:
            list: List of holiday dates in '%Y-%m-%d' format.
        """
        holidays = []
        all_days = ['0', '1', '2', '3', '4', '5', '6']
        for working_hours in \
                self.employee_id.resource_calendar_id.attendance_ids:
            if working_hours.dayofweek in all_days:
                all_days.remove(working_hours.dayofweek)
        for days in all_days:
            if days == '0':
                holidays += self.holiday('W-MON')
            elif days == '1':
                holidays += self.holiday('W-TUE')
            elif days == '2':
                holidays += self.holiday('W-WEN')
            elif days == '3':
                holidays += self.holiday('W-THU')
            elif days == '4':
                holidays += self.holiday('W-FRI')
            elif days == '5':
                holidays += self.holiday('W-SAT')
            elif days == '6':
                holidays += self.holiday('W-SUN')
        return holidays

    @api.model
    def _get_payslip_lines(self):
        """Compute payslip lines including Loss of Pay (LOP) deduction.
        Returns:
            list: List of payslip line dictionaries.
        """
        res = super(HrPayslip, self)._get_payslip_lines()
        amount, lop_amount = 0, 0
        daily_wage = self.contract_id.wage / 30
        for leave in self.env['hr.leave'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('state', '=', 'validate'),
                 ('request_date_from', '>=', self.date_from),
                 ('request_date_to', '<=', self.date_to)]):
            no_of_days, no_of_days_before, no_of_days_after = 0, 0, 0
            prev_flag, next_flag = 0, 0
            leave_type = ''
            previous_date = leave.request_date_from - datetime.timedelta(
                days=1)
            next_date = leave.request_date_to + datetime.timedelta(days=1)
            holidays = self.get_all_holidays()
            for public_holiday in self.env['resource.calendar.leaves'].search(
                    [("resource_id", "=", False)]):
                holiday_duration = len(date_range(
                    start=public_holiday.date_from.strftime('%Y-%m-%d'),
                    end=public_holiday.date_to.strftime('%Y-%m-%d'),
                ).strftime('%Y-%m-%d').tolist())
                if str(previous_date) == str(
                        public_holiday.date_to.strftime('%Y-%m-%d')):
                    no_of_days += holiday_duration
                    no_of_days_before += holiday_duration
                    prev_flag = 1
                if str(next_date) == str(
                        public_holiday.date_from.strftime('%Y-%m-%d')):
                    no_of_days += holiday_duration
                    no_of_days_after += holiday_duration
                    next_flag = 1
            while str(previous_date) in holidays:
                no_of_days += 1
                no_of_days_before += 1
                prev_flag = 1
                previous_date -= datetime.timedelta(days=1)
            while str(next_date) in holidays:
                no_of_days += 1
                no_of_days_after += 1
                next_flag = 1
                next_date += datetime.timedelta(days=1)
            if not next_flag and prev_flag:
                leave_type = 'after_holiday'
            if next_flag and not prev_flag:
                leave_type = 'before_holiday'
            if next_flag and prev_flag:
                leave_type = 'between_holidays'
                if no_of_days_before > no_of_days_after:
                    no_of_days = no_of_days_before + no_of_days_after
                else:
                    no_of_days = no_of_days_after + no_of_days_before
            lop_amount += daily_wage * (
                    self.env['hr.leave.lop'].search([
                        ('no_of_days', '=', no_of_days),
                        ('leave_type', '=', leave_type)],
                    ).deduction_amount / 100)
            amount = lop_amount + (leave.number_of_days_display-1) * daily_wage
        res.append({'sequence': 250,
                    'code': 'LOP',
                    'name': 'Loss of Pay',
                    'salary_rule_id': self.env['hr.salary.rule'].search(
                        [("name", "=", "Deduction"),
                         ("id", "in", self.struct_id.rule_ids.ids)]).id,
                    'contract_id': self.contract_id.id,
                    'employee_id': self.employee_id.id,
                    'amount': -amount,
                    'quantity': 1.0,
                    'rate': 100,
                    'slip_id': self.id
                    })
        return res
