# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#############################################################################
from datetime import timedelta

import pytz

from odoo import models


class HrEmployee(models.Model):
    """Inherit the model hr.employee to add the functionality for retrieving
    public holiday information"""
    _inherit = 'hr.employee'

    def get_public_holidays(self, start_date, end_date):
        """Return ``{'YYYY-MM-DD': True}`` for every day covered by a public
        holiday of the employee (core ``_get_public_holidays``: same company,
        no schedule or the employee's own schedule). Days are taken in the
        employee's timezone, since the datetimes are stored in UTC."""
        all_days = {}
        employee = self or self.env.user.employee_id
        tz = self.env['hr.leave']._dashboard_tz(employee)
        for holiday in employee._get_public_holidays(start_date, end_date):
            day_from = pytz.utc.localize(holiday.date_from).astimezone(tz).date()
            day_to = pytz.utc.localize(holiday.date_to).astimezone(tz).date()
            for day in range((day_to - day_from).days + 1):
                all_days[str(day_from + timedelta(days=day))] = True
        return all_days
