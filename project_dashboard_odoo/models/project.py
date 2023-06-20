# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
import random
from odoo import api, models


class Project(models.Model):
    """

    The ProjectDashboard class provides the data to the js when the dashboard is
    loaded.
        Methods:
            get_tiles_data(self):
                when the page is loaded get the data from different models and
                transfer to the js file.
                return a dictionary variable.
            get_top_timesheet_employees(model_ids):
               getting data for the timesheet graph.
            get_hours_data(self):
                getting data for the hours table.
            get_task_data(self):
                getting data to project task table
            get_project_task_count(self):
                getting data to project task table
            get_color_code(self):
                getting dynamic color code for the graph

    """
    _inherit = 'project.project'

    @api.model
    def get_tiles_data(self):
        """

        Summery:
            when the page is loaded get the data from different models and
            transfer to the js file.
            return a dictionary variable.
        return:
            type:It is a dictionary variable. This dictionary contain data that
            affecting the dashboard view.

        """
        user_employee = self.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
            all_project = self.env['project.project'].search([])
            all_task = self.env['project.task'].search([])
            analytic_project = self.env['account.analytic.line'].search([])
            report_project = self.env['timesheets.analysis.report'].search([])
            margin = sum(report_project.mapped('margin'))
            total_time = sum(analytic_project.mapped('unit_amount'))
            employees = self.env['hr.employee'].search([])

            task = self.env['project.task'].search_read([
                ('sale_order_id', '!=', False)
            ], ['sale_order_id'])
            task_so_ids = [o['sale_order_id'][0] for o in task]
            sale_orders = self.mapped('sale_line_id.order_id') | self.env[
                'sale.order'].browse(task_so_ids)
            project_stage_ids = self.env['project.project.stage'].search([])
            project_stage_list = []
            for project_stage_id in project_stage_ids:
                total_projects = self.env['project.project'].search_count(
                    [('stage_id', '=', project_stage_id.id)])
                project_stage_list.append({
                    'name': project_stage_id.name,
                    'projects': total_projects
                })
            return {
                'total_projects': len(all_project),
                'total_projects_ids': all_project.ids,
                'total_tasks': len(all_task),
                'total_tasks_ids': all_task.ids,
                'total_hours': total_time,
                'total_profitability': margin,
                'total_employees': len(employees),
                'total_sale_orders': len(sale_orders),
                'sale_orders_ids': sale_orders.mapped('id'),
                'project_stage_list': project_stage_list,
                'flag': 1
            }
        else:
            all_project = self.env['project.project'].search(
                [('user_id', '=', self.env.uid)])
            all_task = []
            for task in self.env['project.task'].search([]):
                for assignee in task.user_ids:
                    if assignee.id == self.env.uid:
                        all_task.append(task.id)
            analytic_project = self.env['account.analytic.line'].search(
                [('project_id', 'in', all_project.ids)])
            total_time = sum(analytic_project.mapped('unit_amount'))
            task = self.env['project.task'].search_read([
                ('sale_order_id', '!=', False),
                ('project_id', 'in', all_project.ids)
            ], ['sale_order_id'])
            task_so_ids = [o['sale_order_id'][0] for o in task]
            sale_orders = self.mapped('sale_line_id.order_id') | self.env[
                'sale.order'].browse(task_so_ids)
            project_stage_ids = self.env['project.project.stage'].search([])
            project_stage_list = []
            for project_stage_id in project_stage_ids:
                total_projects = self.env['project.project'].search_count(
                    [('stage_id', '=', project_stage_id.id),
                     ('id', 'in', all_project.ids)])
                project_stage_list.append({
                    'name': project_stage_id.name,
                    'projects': total_projects
                })
            return {
                'total_projects': len(all_project),
                'total_projects_ids': all_project.ids,
                'total_tasks': len(all_task),
                'total_tasks_ids': all_task,
                'total_hours': total_time,
                'total_sale_orders': len(sale_orders),
                'sale_orders_ids': sale_orders.mapped('id'),
                'project_stage_list': project_stage_list,
                'flag': 2
            }

    @api.model
    def get_top_timesheet_employees(self):
        """

        Summery:
            when the page is loaded get the data for the timesheet graph.
        return:
            type:It is a list. This list contain data that affecting the graph
            of employees.

        """
        query = '''select hr_employee.name as employee,sum(unit_amount) as unit
                    from account_analytic_line
                    inner join hr_employee on hr_employee.id =
                    account_analytic_line.employee_id
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
    def get_hours_data(self):
        """

        Summery:
            when the page is loaded get the data for the hours table.
        return:
            type:It is a dictionary variable. This dictionary contain data that
            hours table.

        """
        user_employee = self.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
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
                    WHERE timesheet_invoice_type='non_billable_project' or 
                    timesheet_invoice_type='billable_time'
                    or timesheet_invoice_type='billable_fixed' or 
                    timesheet_invoice_type='non_billable' '''
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
        else:
            all_project = self.env['project.project'].search(
                [('user_id', '=', self.env.uid)]).ids
            analytic_project = self.env['account.analytic.line'].search(
                [('project_id', 'in', all_project)])
            all_hour_recorded = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'non_billable_project')
            all_hour_recorde = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'billable_time')
            all_billable_fix = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'billable_fixed')
            all_non_billable = analytic_project.filtered(
                lambda x: x.timesheet_invoice_type == 'non_billable')

            hour_recorded = [sum(all_hour_recorded.mapped('unit_amount'))]
            hour_recorde = [sum(all_hour_recorde.mapped('unit_amount'))]
            billable_fix = [sum(all_billable_fix.mapped('unit_amount'))]
            non_billable = [sum(all_non_billable.mapped('unit_amount'))]
            total_hr = [sum(hour_recorded + hour_recorde + billable_fix + non_billable)]

            return {
                'hour_recorded': hour_recorded,
                'hour_recorde': hour_recorde,
                'billable_fix': billable_fix,
                'non_billable': non_billable,
                'total_hr': total_hr,
            }

    @api.model
    def get_task_data(self):
        """

        Summery:
            when the page is loaded get the data from different models and
            transfer to the js file.
            return a dictionary variable.
        return:
            type:It is a dictionary variable. This dictionary contain data that
            affecting project task table.

        """
        user_employee = self.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
            self._cr.execute('''select project_task.name as task_name,
            pro.name as project_name from project_task
            Inner join project_project as pro on project_task.project_id = pro.id 
            ORDER BY project_name ASC''')
            data = self._cr.fetchall()
            project_name = []
            for rec in data:
                project_name.append(list(rec))
            return {
                'project': project_name
            }
        else:
            all_project = self.env['project.project'].search(
                [('user_id', '=', self.env.uid)]).ids
            all_tasks = self.env['project.task'].search(
                [('project_id', 'in', all_project)])

            task_project = [[task.name, task.project_id.name] for task in
                            all_tasks]
            return {
                'project': task_project
            }

    @api.model
    def get_project_task_count(self):
        """
        Summery:
            when the page is loaded get the data from different models and
            transfer to the js file.
            return a dictionary variable.
        return:
            type:It is a dictionary variable. This dictionary contain data for
            the project task graph.
        """
        project_name = []
        total_task = []
        colors = []
        user_employee = self.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
            project_ids = self.env['project.project'].search([])
        else:
            project_ids = self.env['project.project'].search(
                [('user_id', '=', self.env.uid)])
        for project_id in project_ids:
            project_name.append(project_id.name)
            task = self.env['project.task'].search_count(
                [('project_id', '=', project_id.id)])
            total_task.append(task)
            color_code = self.get_color_code()
            colors.append(color_code)
        return {
            'project': project_name,
            'task': total_task,
            'color': colors
        }

    def get_color_code(self):
        """
        Summery:
            the function is for creating the dynamic color code.
        return:
            type:variable containing color code.
        """
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        return color
