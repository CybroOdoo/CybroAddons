# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
###############################################################################
import re

import pandas
from datetime import date, timedelta
from odoo import api, fields, models
from odoo.http import request
from odoo.tools import date_utils


class HrEmployee(models.Model):
    """This module extends the 'hr.employee' model of  Odoo Employees Module.
     It adds a new method called 'get_employee_leave_data', which is used to
     retrieve data for the dashboard."""
    _inherit = 'hr.employee'
    _check_company_auto = True

    @api.model
    def get_employee_leave_data(self, option):
        """Returns data to the dashboard"""
        employee_data = []
        res_config = self.env['res.config.settings'].search([], limit=1,
                                                            order='id desc')
        dates = False
        if option == 'this_week':
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today(), 'week'),
                date_utils.end_of(fields.Date.today(), 'week')
                - timedelta(
                    days=0),
                freq='d').strftime(
                "%Y-%m-%d").tolist()
        elif option == 'this_month':
            dates = pandas.date_range(
                date_utils.start_of(fields.Date.today(), 'month'),
                date_utils.end_of(fields.Date.today(), 'month')
                - timedelta(
                    days=0),
                freq='d').strftime(
                "%Y-%m-%d").tolist()
        elif option == 'last_15_days':
            dates = [str(date.today() - timedelta(days=day))
                     for day in range(15)]

        cids = request.httprequest.cookies.get('cids', '')
        split_cids = re.split(r'[,-]', cids)
        allowed_company_ids = [int(cid) for cid in split_cids if cid.isdigit()]
        for employee in self.env['hr.employee'].search(
                [('company_id', '=', allowed_company_ids)]):
            leave_data = []
            employee_present_dates = []
            employee_leave_dates = []
            total_absent_count = 0
            query = ("""
                SELECT hl.id,employee_id,request_date_from,request_date_to,
                hlt.leave_code,hlt.color
                FROM hr_leave hl
				INNER JOIN hr_leave_type hlt ON hlt.id = hl.holiday_status_id 
                WHERE hl.state = 'validate' AND employee_id = '%s'"""
                     % employee.id)
            self._cr.execute(query)
            all_leave_rec = self._cr.dictfetchall()
            for leave in all_leave_rec:
                leave_dates = pandas.date_range(
                    leave.get('request_date_from'),
                    leave.get('request_date_to') - timedelta(
                        days=0),
                    freq='d').strftime(
                    "%Y-%m-%d").tolist()
                leave_dates.insert(0, leave.get('leave_code'))
                leave_dates.insert(1, leave.get('color'))
                for leave_date in leave_dates:
                    if leave_date in dates:
                        employee_leave_dates.append(
                            leave_date
                        )
            for employee_check_in in employee.attendance_ids:
                employee_present_dates.append(
                    str(employee_check_in.check_in.date()))
            for leave_date in dates:
                color = "#ffffff"
                marks = self.env[
                    'res.config.settings'].search([], limit=1)
                state = None
                if marks:
                    if leave_date in employee_present_dates:
                        state = res_config.present
                    else:
                        state = res_config.absent
                if leave_date in employee_leave_dates:
                    state = leave_dates[0]
                    color = "#F06050" if leave_dates[1] == 1 \
                        else "#F4A460" if leave_dates[1] == 2 \
                        else "#F7CD1F" if leave_dates[1] == 3 \
                        else "#6CC1ED" if leave_dates[1] == 4 \
                        else "#814968" if leave_dates[1] == 5 \
                        else "#EB7E7F" if leave_dates[1] == 6 \
                        else "#2C8397" if leave_dates[1] == 7 \
                        else "#475577" if leave_dates[1] == 8 \
                        else "#D6145F" if leave_dates[1] == 9 \
                        else "#30C381" if leave_dates[1] == 10 \
                        else "#9365B8" if leave_dates[1] == 11 \
                        else "#ffffff"
                    total_absent_count += 1
                leave_data.append({
                    'id': employee.id,
                    'leave_date': leave_date,
                    'state': state,
                    'color': color
                })
            employee_data.append({
                'id': employee.id,
                'name': employee.name,
                'leave_data': leave_data[::-1],
                'total_absent_count': total_absent_count
            })
        return {
            'employee_data': employee_data,
            'filtered_duration_dates': dates[::-1]
        }
