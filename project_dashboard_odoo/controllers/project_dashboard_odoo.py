# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mruthul Raj @cybrosys(odoo@cybrosys.com)
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
###############################################################################
import datetime
from odoo import http
from odoo.http import request


class ProjectFilter(http.Controller):
    """The ProjectFilter class provides the filter option to the js.
    When applying the filter returns the corresponding data."""

    @http.route('/project/task/count', auth='public', type='json')
    def get_project_task_count(self):
        """Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data for
            the project task graph."""
        project_name = []
        total_task = []
        colors = []
        user_employee = request.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
            project_ids = request.env['project.project'].search([])
        else:
            project_ids = request.env['project.project'].search(
                [('user_id', '=', request.env.uid)])
        for project_id in project_ids:
            project_name.append(project_id.name)
            task = request.env['project.task'].search_count(
                [('project_id', '=', project_id.id)])
            total_task.append(task)
            color_code = request.env['project.project'].get_color_code()
            colors.append(color_code)
        return {
            'project': project_name,
            'task': total_task,
            'color': colors
        }

    @http.route('/employee/timesheet', auth='public', type='json')
    def get_top_timesheet_employees(self):
        """Summary:
            when the page is loaded, get the data for the timesheet graph.
        Return:
            type:It is a list. This list contains data that affects the graph
            of employees."""
        query = '''select hr_employee.name as employee,sum(unit_amount) as unit
                    from account_analytic_line
                    inner join hr_employee on hr_employee.id =
                    account_analytic_line.employee_id
                    group by hr_employee.id ORDER 
                    BY unit DESC Limit 10 '''
        request._cr.execute(query)
        top_product = request._cr.dictfetchall()
        unit = [record.get('unit') for record in top_product]
        employee = [record.get('employee') for record in top_product]
        return [unit, employee]

    @http.route('/project/filter', auth='public', type='json')
    def project_filter(self):
        """Summary:
            transferring data to the selection field that works as a filter
        Returns:
            type:list of lists, it contains the data for the corresponding
            filter."""
        project_list = []
        employee_list = []
        project_ids = request.env['project.project'].search([])
        employee_ids = request.env['hr.employee'].search([])
        # getting partner data
        for employee_id in employee_ids:
            dic = {'name': employee_id.name,
                   'id': employee_id.id}
            employee_list.append(dic)
        for project_id in project_ids:
            dic = {'name': project_id.name,
                   'id': project_id.id}
            project_list.append(dic)
        return [project_list, employee_list]

    @http.route('/project/filter-apply', auth='public', type='json')
    def project_filter_apply(self, **kw):
        """Summary:
            transferring data after filter 9th applied
        Args:
            kw(dict):This parameter contains the value of selection field
        Returns:
            type:dict, it contains the data for the corresponding
            filtrated transferring data to ui after filtration."""
        data = kw['data']
        # checking the employee selected or not
        if data['employee'] == 'null':
            emp_selected = [employee.id for employee in
                            request.env['hr.employee'].search([])]
        else:
            emp_selected = [int(data['employee'])]
        start_date = data['start_date']
        end_date = data['end_date']
        # checking the dates are selected or not
        if start_date != 'null' and end_date != 'null':
            start_date = datetime.datetime.strptime(start_date,
                                                    "%Y-%m-%d").date()
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search(
                                    [('date_start', '>', start_date),
                                     ('date_start', '<', end_date)])]
            else:
                pro_selected = [int(data['project'])]
        elif start_date == 'null' and end_date != 'null':
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search(
                                    [('date_start', '<', end_date)])]
            else:
                pro_selected = [int(data['project'])]
        elif start_date != 'null' and end_date == 'null':
            start_date = datetime.datetime.strptime(start_date,
                                                    "%Y-%m-%d").date()
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search(
                                    [('date_start', '>', start_date)])]
            else:
                pro_selected = [int(data['project'])]
        else:
            if data['project'] == 'null':
                pro_selected = [project.id for project in
                                request.env['project.project'].search([])]
            else:
                pro_selected = [int(data['project'])]
        report_project = request.env['timesheets.analysis.report'].search(
            [('project_id', 'in', pro_selected),
             ('employee_id', 'in', emp_selected)])
        analytic_project = request.env['account.analytic.line'].search(
            [('project_id', 'in', pro_selected),
             ('employee_id', 'in', emp_selected)])
        margin = round(sum(report_project.mapped('margin')), 2)
        sale_orders = []
        for rec in analytic_project:
            if rec.order_id.id and rec.order_id.id not in sale_orders:
                sale_orders.append(rec.order_id.id)
        total_time = sum(analytic_project.mapped('unit_amount'))
        return {
            'total_project': pro_selected,
            'total_emp': emp_selected,
            'total_task': [rec.id for rec in request.env['project.task'].search(
                [('project_id', 'in', pro_selected)])],
            'hours_recorded': total_time,
            'list_hours_recorded': [rec.id for rec in analytic_project],
            'total_margin': margin,
            'total_so': sale_orders
        }

    @http.route('/get/tiles/data', auth='public', type='json')
    def get_tiles_data(self):
        """Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data that
             affects the dashboard view."""
        user_employee = request.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
            all_project = request.env['project.project'].search([])
            all_task = request.env['project.task'].search([])
            analytic_project = request.env['account.analytic.line'].search([])
            report_project = request.env['timesheets.analysis.report'].search(
                [])
            margin = round(sum(report_project.mapped('margin')), 2)
            total_time = sum(analytic_project.mapped('unit_amount'))
            employees = request.env['hr.employee'].search([])
            task = request.env['project.task'].sudo().search_read([
                ('sale_order_id', '!=', False)
            ], ['sale_order_id'])
            task_so_ids = [o['sale_order_id'][0] for o in task]
            sale_orders = request.env['sale.order'].browse(task_so_ids)
            project_stage_ids = request.env['project.project.stage'].search([])
            project_stage_list = []
            for project_stage_id in project_stage_ids:
                total_projects = request.env[
                    'project.project'].sudo().search_count(
                    [('stage_id', '=', project_stage_id.id)])
                project_stage_list.append({'name': project_stage_id.name,
                                           'projects': total_projects})
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
                'flag': 1}
        else:
            all_project = request.env['project.project'].search(
                [('user_id', '=', request.env.uid)])
            all_task = []
            for task in request.env['project.task'].search([]):
                for assignee in task.user_ids:
                    if assignee.id == request.env.uid:
                        all_task.append(task.id)
            analytic_project = request.env['account.analytic.line'].search(
                [('project_id', 'in', all_project.ids)])
            total_time = sum(analytic_project.mapped('unit_amount'))
            task = request.env['project.task'].sudo().search_read([
                ('sale_order_id', '!=', False),
                ('project_id', 'in', all_project.ids)
            ], ['sale_order_id'])
            task_so_ids = [o['sale_order_id'][0] for o in task]
            sale_orders = request.mapped('sale_line_id.order_id') | request.env[
                'sale.order'].browse(task_so_ids)
            project_stage_ids = request.env['project.project.stage'].search([])
            project_stage_list = []
            for project_stage_id in project_stage_ids:
                total_projects = request.env['project.project'].search_count(
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
                'flag': 2}

    @http.route('/get/hours', auth='public', type='json')
    def get_hours_data(self):
        """Summary:
            when the page is loaded get the data for the hour table.
        Return:
            type:It is a dictionary variable. This dictionary contains data that
            hours table."""
        user_employee = request.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
            query = '''SELECT sum(unit_amount) as hour_recorded FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='non_billable_project' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            hour_recorded = []
            for record in data:
                hour_recorded.append(record.get('hour_recorded'))
            query = '''SELECT sum(unit_amount) as hour_recorde FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='billable_time' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            hour_recorde = []
            for record in data:
                hour_recorde.append(record.get('hour_recorde'))
            query = '''SELECT sum(unit_amount) as billable_fix FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='billable_fixed' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            billable_fix = []
            for record in data:
                billable_fix.append(record.get('billable_fix'))
            query = '''SELECT sum(unit_amount) as non_billable FROM 
            account_analytic_line WHERE timesheet_invoice_type='non_billable' 
            '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
            non_billable = []
            for record in data:
                non_billable.append(record.get('non_billable'))
            query = '''SELECT sum(unit_amount) as total_hr FROM 
            account_analytic_line WHERE 
            timesheet_invoice_type='non_billable_project' or
            timesheet_invoice_type='billable_time' or 
            timesheet_invoice_type='billable_fixed' or 
            timesheet_invoice_type='non_billable' '''
            request._cr.execute(query)
            data = request._cr.dictfetchall()
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
            all_project = request.env['project.project'].search(
                [('user_id', '=', request.env.uid)]).ids
            analytic_project = request.env['account.analytic.line'].search(
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
            total_hr = [
                sum(hour_recorded + hour_recorde + billable_fix + non_billable)]
            return {
                'hour_recorded': hour_recorded,
                'hour_recorde': hour_recorde,
                'billable_fix': billable_fix,
                'non_billable': non_billable,
                'total_hr': total_hr,
            }

    @http.route('/get/task/data', auth='public', type='json')
    def get_task_data(self):
        """
        Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data that
            affecting project task table."""
        user_employee = request.env.user.partner_id
        if user_employee.user_has_groups('project.group_project_manager'):
            request._cr.execute('''select project_task.name as task_name,
            pro.name as project_name from project_task
            Inner join project_project as pro on project_task.project_id 
            = pro.id ORDER BY project_name ASC''')
            data = request._cr.fetchall()
            project_name = []
            for rec in data:
                project_name.append(list(rec))
            return {
                'project': project_name
            }
        else:
            all_project = request.env['project.project'].search(
                [('user_id', '=', request.env.uid)]).ids
            all_tasks = request.env['project.task'].search(
                [('project_id', 'in', all_project)])
            task_project = [[task.name, task.project_id.name] for task in
                            all_tasks]
            return {
                'project': task_project
            }
