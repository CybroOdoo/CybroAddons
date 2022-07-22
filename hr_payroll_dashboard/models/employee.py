#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions(odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import timedelta, datetime, date
from collections import defaultdict
from dateutil.relativedelta import relativedelta
import pandas as pd
from pytz import utc
from odoo.tools import float_utils
from odoo import models, fields, api, _
from odoo.http import request

ROUNDING_FACTOR = 16


class Employee(models.Model):
    _inherit = 'hr.employee'

    is_manager = fields.Boolean(compute='_compute_is_manager')

    def _compute_is_manager(self):
        """Compute function for checking whether it is a manager or not"""
        for rec in self:
            if rec.env.user.has_group('hr_payroll_community.group_hr_payroll_community_manager'):
                rec.is_manager = True
            else:
                rec.is_manager = False

    @api.model
    def get_user_employee_info(self):
        """To get the employee information"""
        uid = request.session.uid
        employee_id = self.env['hr.employee'].sudo().search([
            ('user_id', '=', uid)], limit=1)
        employee = self.env['hr.employee'].sudo().search_read([
            ('user_id', '=', uid)], limit=1)
        attendance_count = self.env['hr.attendance'].sudo().search(
            [('employee_id', '=', employee_id.id),
             ('attendance_date', '=', date.today())])
        manager_attendance_count = self.env['hr.attendance'].sudo().search(
            [('attendance_date', '=', date.today())])
        leave_request_count = self.env['hr.leave'].sudo().search(
            [('employee_id', '=', employee_id.id),
             ('request_date_from', '=', date.today())])
        manager_leave_request = self.env['hr.leave'].sudo().search(
            [('request_date_from', '=', date.today())])
        employee_contracts = self.env['hr.contract'].sudo().search([
            ('employee_id', '=', employee_id.id)])
        payslips = self.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee_id.id)])
        salary_rules = self.env['hr.salary.rule'].sudo().search([])
        salary_structures = self.env['hr.payroll.structure'].sudo().search([])
        salary_rule_count = len(salary_rules)
        salary_structure_count = len(salary_structures)
        emp_leave = len(manager_leave_request) if employee_id.is_manager \
            else len(leave_request_count)
        payslip_count = len(payslips) if not employee_id.is_manager \
            else len(self.env['hr.payslip'].sudo().search([]))
        emp_contracts_count = len(employee_contracts) \
            if not employee_id.is_manager else len(
                self.env['hr.contract'].sudo().search([]))
        attendance_today = len(manager_attendance_count) \
            if employee_id.is_manager else len(attendance_count)
        if employee:
            data = {
                'emp_timesheets': attendance_today,
                'emp_leave': emp_leave,
                'emp_contracts_count': emp_contracts_count,
                'payslip_count': payslip_count,
                'leave_requests': leave_request_count,
                'salary_rule_count': salary_rule_count,
                'salary_structure_count': salary_structure_count,
                'attendance_state': employee[0]['attendance_state'],
            }
            employee[0].update(data)
        return employee

    def get_work_days_dashboard(self, from_datetime, to_datetime,
                                compute_leaves=False, calendar=None,
                                domain=None):
        """To get the work days count"""
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals(from_full, to_full,
                                                   resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals:
            day_total[start.date()] += (stop - start).total_seconds() / 3600
        if compute_leaves:
            intervals = calendar._work_intervals(from_datetime, to_datetime,
                                                 resource, domain)
        else:
            intervals = calendar._attendance_intervals(from_datetime,
                                                       to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return days

    @api.model
    def get_department_leave(self):
        """return department wise leave details"""
        month_list = []
        graph_result = []
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read([
            ('user_id', '=', uid)], limit=1)

        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        self.env.cr.execute("""select id, name from hr_department 
            where active=True""")
        departments = self.env.cr.dictfetchall()
        department_list = [x['name'] for x in departments]
        for month in month_list:
            leave = {}
            for dept in departments:
                leave[dept['name']] = 0
            vals = {
                'l_month': month,
                'leave': leave
            }
            graph_result.append(vals)
        employee_id = self.env['hr.employee'].browse(employee[0]['id'])

        sql = """
            SELECT h.id, h.employee_id,h.department_id
                 , extract('month' FROM y)::int AS leave_month
                 , to_char(y, 'Month YYYY') as month_year
                 , GREATEST(y                    , h.date_from) AS date_from
                 , LEAST   (y + interval '1 month', h.date_to)   AS date_to
            FROM  (select * from hr_leave where state = 'validate') h
                 , generate_series(date_trunc('month', date_from::timestamp)
                                 , date_trunc('month', date_to::timestamp)
                                 , interval '1 month') y
            where date_trunc('month', GREATEST(y , h.date_from)) >= 
            date_trunc('month', now()) - interval '6 month' and
            date_trunc('month', GREATEST(y , h.date_from)) <= 
            date_trunc('month', now())
            and h.department_id is not null
            """
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()
        leave_lines = []
        for line in results:
            employee = self.browse(line['employee_id'])
            from_dt = fields.Datetime.from_string(line['date_from'])
            to_dt = fields.Datetime.from_string(line['date_to'])
            days = employee.get_work_days_dashboard(from_dt, to_dt)
            line['days'] = days
            vals = {
                'department': line['department_id'],
                'l_month': line['month_year'],
                'days': days
            }
            leave_lines.append(vals)
        if leave_lines:
            df = pd.DataFrame(leave_lines)
            rf = df.groupby(['l_month', 'department']).sum()
            result_lines = rf.to_dict('index')
            for month in month_list:
                for line in result_lines:
                    if month.replace(' ', '') == line[0].replace(' ', ''):
                        match = list(filter(lambda d: d['l_month'] in [month],
                                            graph_result))[0]['leave']
                        dept_name = self.env['hr.department'].browse(
                            line[1]).name
                        if match:
                            match[dept_name] = result_lines[line]['days']
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[:3] \
                                + " " + result['l_month'].split(' ')[1:2][0]
        return graph_result, department_list

    @api.model
    def get_employee_expense(self):
        """return employee expense details"""
        month_list = []
        graph_result = []
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read([
            ('user_id', '=', uid)], limit=1)

        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        self.env.cr.execute("""select id, name from hr_employee 
        where active=True""")
        departments = self.env.cr.dictfetchall()
        department_list = [x['name'] for x in departments]
        for month in month_list:
            leave = {}
            for dept in departments:
                leave[dept['name']] = 0
            vals = {
                'l_month': month,
                'leave': leave
            }
            graph_result.append(vals)
        employee_id = self.env['hr.employee'].browse(employee[0]['id'])

        sql = """
                SELECT h.id, h.employee_id,h.date,
                extract('month' FROM h.date)::int AS leave_month,
                to_char(h.date, 'Month YYYY') as month_year 
                FROM  (select * from hr_expense where state = 'approved') h 
                """
        self.env.cr.execute(sql, (employee[0]['id'],))

        results = self.env.cr.dictfetchall()
        leave_lines = []
        for line in results:
            employee = self.browse(line['employee_id'])
            from_dt = fields.Datetime.from_string(line['date'])
            to_dt = fields.Datetime.from_string(line['date'])
            days = employee.get_work_days_dashboard(from_dt, to_dt)
            line['days'] = days
            vals = {
                'department': line['employee_id'],
                'l_month': line['month_year'],
                'days': days
            }
            leave_lines.append(vals)
        if leave_lines:
            df = pd.DataFrame(leave_lines)
            rf = df.groupby(['l_month', 'department']).sum()
            result_lines = rf.to_dict('index')
            for month in month_list:
                for line in result_lines:
                    if month.replace(' ', '') == line[0].replace(' ', ''):
                        match = list(filter(lambda d: d['l_month'] in [month],
                                            graph_result))[0]['leave']
                        dept_name = self.env['hr.department'].browse(
                            line[1]).name
                        if match:
                            match[dept_name] = result_lines[line]['days']
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[:3] \
                                + " " + result['l_month'].split(' ')[1:2][0]
        return graph_result, department_list

    @api.model
    def employee_leave_trend(self):
        """return employee monthly leave details"""
        leave_lines = []
        month_list = []
        graph_result = []
        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read([
            ('user_id', '=', uid)], limit=1)
        for month in month_list:
            vals = {
                'l_month': month,
                'leave': 0
            }
            graph_result.append(vals)
        sql = """
            SELECT h.id, h.employee_id
                 , extract('month' FROM y)::int AS leave_month
                 , to_char(y, 'Month YYYY') as month_year
                 , GREATEST(y                    , h.date_from) AS date_from
                 , LEAST   (y + interval '1 month', h.date_to)   AS date_to
            FROM  (select * from hr_leave where state = 'validate') h
                 , generate_series(date_trunc('month', date_from::timestamp)
                                 , date_trunc('month', date_to::timestamp)
                                 , interval '1 month') y
            where date_trunc('month', GREATEST(y , h.date_from)) >= 
            date_trunc('month', now()) - interval '6 month' and
            date_trunc('month', GREATEST(y , h.date_from)) <= 
            date_trunc('month', now())
            and h.employee_id = %s
            """
        self.env.cr.execute(sql, (employee[0]['id'],))
        results = self.env.cr.dictfetchall()
        for line in results:
            employee = self.browse(line['employee_id'])
            from_dt = fields.Datetime.from_string(line['date_from'])
            to_dt = fields.Datetime.from_string(line['date_to'])
            days = employee.get_work_days_dashboard(from_dt, to_dt)
            line['days'] = days
            vals = {
                'l_month': line['month_year'],
                'days': days
            }
            leave_lines.append(vals)
        if leave_lines:
            df = pd.DataFrame(leave_lines)
            rf = df.groupby(['l_month']).sum()
            result_lines = rf.to_dict('index')
            for line in result_lines:
                match = list(filter(lambda d: d['l_month'].replace(
                    ' ', '') == line.replace(' ', ''), graph_result))
                if match:
                    match[0]['leave'] = result_lines[line]['days']
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[:3] \
                                + " " + result['l_month'].split(' ')[1:2][0]
        return graph_result


class Contract(models.Model):
    _inherit = 'hr.contract'

    state_label = fields.Char(compute="compute_state_label", store=True)

    @api.depends('state')
    def compute_state_label(self):
        """Compute to get the label value of the contract state"""
        for record in self:
            record.state_label = dict(self._fields['state'].selection).get(
                record.state)

    @api.model
    def get_employee_contract(self):
        """return employees contract details"""
        cr = self._cr
        cr.execute("""SELECT hr_contract.state_label,count(*) 
        FROM hr_contract 
        JOIN hr_employee ON hr_employee.id=hr_contract.employee_id 
        GROUP BY hr_contract.state_label""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    state_label = fields.Char(compute="compute_state_label", store=True)

    @api.depends('state')
    def compute_state_label(self):
        """Compute function for the expense state label"""
        for record in self:
            record.state_label = dict(self._fields['state'].selection).get(
                record.state)

    @api.model
    def get_employee_expense(self):
        """return employee expense details"""
        cr = self._cr
        month_list = []
        approved_trend = []

        for i in range(11, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        for month in month_list:
            vals = {
                'l_month': month,
                'count': 0
            }
            approved_trend.append(vals)
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read([
            ('user_id', '=', uid)], limit=1)
        employee_id = self.env['hr.employee'].browse(employee[0]['id'])
        if not employee_id.is_manager:
            sql = ('''select to_char(date, 'Month YYYY') as l_month, 
                    count(id) from hr_expense
                    WHERE date BETWEEN CURRENT_DATE - INTERVAL '12 months'
                    AND CURRENT_DATE + interval '1 month - 1 day' 
                    AND hr_expense.employee_id = %s
                    group by l_month''')
            self.env.cr.execute(sql, (employee[0]['id'],))
        else:
            sql = ('''select to_char(date, 'Month YYYY') as l_month, 
            count(id) from hr_expense WHERE date 
            BETWEEN CURRENT_DATE - INTERVAL 
            '12 months' AND CURRENT_DATE + interval '1 month - 1 day' 
            group by l_month''')
            self.env.cr.execute(sql)
        approved_data = cr.fetchall()
        for line in approved_data:
            match = list(filter(lambda d: d['l_month'].replace(
                ' ', '') == line[0].replace(' ', ''), approved_trend))
            if match:
                match[0]['count'] = line[1]

        for expense in approved_trend:
            expense['l_month'] = expense[
                                     'l_month'].split(' ')[:1][0].strip()[:3]

        graph_result = [{

            'values': approved_trend
        }]
        return graph_result


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    attendance_date = fields.Date(compute="compute_attendance_date",
                                  store=True)

    @api.depends('check_in')
    def compute_attendance_date(self):
        """Compute function for the attendance date"""
        for rec in self:
            if rec.check_in:
                rec.attendance_date = rec.check_in.date()
