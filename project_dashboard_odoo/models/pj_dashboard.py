# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

from odoo import models, api
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import calendar


class PosDashboard(models.Model):
    _inherit = 'project.project'

    @api.model
    def get_tiles_data(self):
        all_project = self.env['project.project'].search([])
        all_task = self.env['project.task'].search([])
        analytic_project = self.env['account.analytic.line'].search([])
        report_project = self.env['project.profitability.report'].search([])
        to_invoice = sum(report_project.mapped('amount_untaxed_to_invoice'))
        invoice = sum(report_project.mapped('amount_untaxed_invoiced'))
        timesheet_cost = sum(report_project.mapped('timesheet_cost'))
        other_cost = sum(report_project.mapped('expense_cost'))
        profitability = to_invoice + invoice + timesheet_cost + other_cost
        total_time = sum(analytic_project.mapped('unit_amount'))
        employees = self.env['hr.employee'].search([])

        task = self.env['project.task'].search_read([
            ('sale_order_id', '!=', False)
        ], ['sale_order_id'])
        task_so_ids = [o['sale_order_id'][0] for o in task]
        sale_orders = self.mapped('sale_line_id.order_id') | self.env['sale.order'].browse(task_so_ids)
        return {
            'total_projects': len(all_project),
            'total_tasks': len(all_task),
            'total_hours': total_time,
            'total_profitability': profitability,
            'total_employees': len(employees),
            'total_sale_orders': len(sale_orders)
        }

    @api.model
    def get_top_timesheet_employees(self):

        query = '''select hr_employee.name as employee,sum(unit_amount) as unit
                    from account_analytic_line
                    inner join hr_employee on hr_employee.id =account_analytic_line.employee_id
                    group by hr_employee.id ORDER 
                    BY unit DESC Limit 10 '''

        self._cr.execute(query)
        top_product = self._cr.dictfetchall()

        unit = []
        for record in top_product:
            unit.append(record.get('unit'))
        employee = []
        for record in top_product:
            employee.append(record.get('employee'))
        final = [unit, employee]
        return final

    @api.model
    def get_project_task(self):
        cr = self._cr
        cr.execute("""select project_id, project_project.name,count(*)
        from project_task join project_project on project_project.id=project_task.project_id
        group by project_task.project_id,project_project.name""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][1], 'value': dat[i][2]})
        return data

    @api.model
    def project_profitability_trend(self):
        leave_lines = []
        month_list = []
        graph_result = []
        for i in range(6, -2, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        for month in month_list:
            vals = {
                'l_month': month,
                'leave': 0
            }

            graph_result.append(vals)

        sql = """SELECT h.id,h.margin,
                      to_char(y, 'YYYY') as month_year
                FROM  (select * from project_profitability_report) h
                     ,date_trunc('year', line_date)y"""

        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()
        for line in results:
            days = line['margin']
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
                match = list(graph_result)
                if match:
                    match[0]['leave'] = result_lines[line]['days']
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[:3] + " " + \
                                result['l_month'].split(' ')[1:2][0]

        return graph_result

    @api.model
    def get_profitability_details(self):
        query = '''select sum(margin) as payment_details from project_profitability_report'''
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        payment_details = []
        for record in data:
            payment_details.append(record.get('payment_details'))

        return {
            'payment_details': payment_details,
        }

    @api.model
    def get_details(self):
        query = '''select sum(amount_untaxed_invoiced) as invoiced,
            sum(amount_untaxed_to_invoice) as to_invoice,sum(timesheet_cost) as time_cost,
            sum(expense_cost) as expen_cost,
            sum(margin) as payment_details from project_profitability_report'''
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        invoiced = []
        for record in data:
            invoiced.append(record.get('invoiced'))

        to_invoice = []
        for record in data:
            to_invoice.append(record.get('to_invoice'))

        time_cost = []
        for record in data:
            time_cost.append(record.get('time_cost'))

        expen_cost = []
        for record in data:
            expen_cost.append(record.get('expen_cost'))

        payment_details = []
        for record in data:
            payment_details.append(record.get('payment_details'))

        return {
            'invoiced': invoiced,
            'to_invoice': to_invoice,
            'time_cost': time_cost,
            'expen_cost': expen_cost,
            'payment_details': payment_details,
        }

    @api.model
    def get_hours_data(self):
        query = '''SELECT sum(unit_amount) as hour_recorded FROM account_analytic_line
        WHERE timesheet_invoice_type='non_billable_project' '''
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        hour_recorded = []
        for record in data:
            hour_recorded.append(record.get('hour_recorded'))

        query = '''SELECT sum(unit_amount) as hour_recorde FROM account_analytic_line
                WHERE timesheet_invoice_type='billable_time' '''
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        hour_recorde = []
        for record in data:
            hour_recorde.append(record.get('hour_recorde'))

        query = '''SELECT sum(unit_amount) as billable_fix FROM account_analytic_line
                       WHERE timesheet_invoice_type='billable_fixed' '''
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        billable_fix = []
        for record in data:
            billable_fix.append(record.get('billable_fix'))

        query = '''SELECT sum(unit_amount) as non_billable FROM account_analytic_line
                               WHERE timesheet_invoice_type='non_billable' '''
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        non_billable = []
        for record in data:
            non_billable.append(record.get('non_billable'))

        query = '''SELECT sum(unit_amount) as total_hr FROM account_analytic_line
                WHERE timesheet_invoice_type='non_billable_project' or timesheet_invoice_type='billable_time'
                or timesheet_invoice_type='billable_fixed' or timesheet_invoice_type='non_billable' '''
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        total_hr = []
        for record in data:
            total_hr.append(record.get('total_hr'))

        return {
            'hour_recorded': hour_recorded,
            'hour_recorde': hour_recorde,
            'billable_fix': billable_fix,
            'non_billable': non_billable,
            'total_hr': total_hr,
        }

    @api.model
    def get_income_this_year(self):

        month_list = []
        for i in range(11, -1, -1):
            l_month = datetime.now() - relativedelta(months=i)
            text = format(l_month, '%B')
            month_list.append(text)

        states_arg = ""

        self._cr.execute(('''select sum(margin) as income ,to_char(project_profitability_report.line_date, 'Month') 
                            as month from project_profitability_report where 
                            to_char(DATE(NOW()), 'YY') = to_char(project_profitability_report.line_date, 'YY')
                            %s  group by month ''') % (states_arg))
        record = self._cr.dictfetchall()

        records = []
        for month in month_list:
            last_month_inc = list(filter(lambda m: m['month'].strip() == month, record))

            if not last_month_inc:
                records.append({
                    'month': month,
                    'profit': 0.0,
                })

            else:

                last_month_inc[0].update({
                    'profit': last_month_inc[0]['income']
                })
                records.append(last_month_inc[0])

        month = []
        profit = []
        for rec in records:
            month.append(rec['month'])
            profit.append(rec['profit'])
        return {
            'profit': profit,
            'month': month,
        }

    @api.model
    def get_income_last_year(self):
        month_list = []
        for i in range(11, -1, -1):
            l_month = datetime.now() - relativedelta(months=i)
            text = format(l_month, '%B')
            month_list.append(text)

        states_arg = ""

        self._cr.execute(('''select sum(margin) as income ,to_char(project_profitability_report.line_date, 'Month')  
                        as month from project_profitability_report where
                        Extract(year FROM project_profitability_report.line_date) = Extract(year FROM DATE(NOW())) -1
                                    %s group by month ''') % (states_arg))
        record = self._cr.dictfetchall()

        records = []
        for month in month_list:
            last_month_inc = list(filter(lambda m: m['month'].strip() == month, record))
            if not last_month_inc:
                records.append({
                    'month': month,
                    'profit': 0.0,

                })

            else:

                last_month_inc[0].update({
                    'profit': last_month_inc[0]['income']
                })
                records.append(last_month_inc[0])

        month = []
        profit = []
        for rec in records:
            month.append(rec['month'])
            profit.append(rec['profit'])
        return {

            'month': month,
            'profit': profit,
        }

    @api.model
    def get_income_this_month(self):
        states_arg = ""
        day_list = []
        now = datetime.now()
        day = calendar.monthrange(now.year, now.month)[1]
        for x in range(1, day + 1):
            day_list.append(x)
        self._cr.execute(('''select sum(margin) as income ,cast(to_char(project_profitability_report.line_date, 'DD')
                                as int) as date from project_profitability_report where   
                                Extract(month FROM project_profitability_report.line_date) = Extract(month FROM DATE(NOW()))  
                                AND Extract(YEAR FROM project_profitability_report.line_date) = Extract(YEAR FROM DATE(NOW()))
                                %s  group by date  ''') % (states_arg))

        record = self._cr.dictfetchall()

        records = []
        for date in day_list:
            last_month_inc = list(filter(lambda m: m['date'] == date, record))
            if not last_month_inc:
                records.append({
                    'date': date,
                    'income': 0.0,
                    'profit': 0.0
                })

            else:

                last_month_inc[0].update({
                    'profit': last_month_inc[0]['income']
                })
                records.append(last_month_inc[0])
        date = []
        profit = []
        for rec in records:
            date.append(rec['date'])
            profit.append(rec['profit'])
        return {
            'date': date,
            'profit': profit

        }

    @api.model
    def get_task_data(self):
        self._cr.execute('''select project_task.name as task_name,pro.name as project_name from project_task
          Inner join project_project as pro on project_task.project_id = pro.id ORDER BY project_name ASC''')
        data = self._cr.fetchall()
        project_name = []
        for rec in data:
            b = list(rec)
            project_name.append(b)
        return {
            'project': project_name
        }
