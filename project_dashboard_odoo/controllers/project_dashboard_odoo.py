# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import datetime as dt
import logging

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class ProjectFilter(http.Controller):
    """The ProjectFilter class provides the filter option to the js.
    When applying the filter returns the corresponding data."""

    def _init_request_context(self, **kw):
        """Ensure request.env has the active allowed_company_ids set."""
        context = kw.get('context') or {}
        allowed_company_ids = context.get('allowed_company_ids')
        if not allowed_company_ids:
            try:
                cids = None
                if hasattr(request, 'cookies') and request.cookies:
                    cids = request.cookies.get('cids')
                elif hasattr(request, 'httprequest') and request.httprequest.cookies:
                    cids = request.httprequest.cookies.get('cids')
                if cids:
                    if isinstance(cids, str):
                        allowed_company_ids = [int(cid) for cid in cids.split('-') if cid.isdigit()]
                    elif isinstance(cids, int):
                        allowed_company_ids = [cids]
                    elif isinstance(cids, list):
                        allowed_company_ids = [int(cid) for cid in cids if str(cid).isdigit()]
            except (RuntimeError, ValueError, KeyError, TypeError) as err:
                _logger.debug("Failed to determine allowed_company_ids: %s", err)
                allowed_company_ids = []
        if allowed_company_ids:
            try:
                request.update_context(allowed_company_ids=allowed_company_ids)
            except (RuntimeError, ValueError, TypeError) as err:
                _logger.debug("Failed to update context with allowed_company_ids: %s", err)

    def _get_project_domain(self):
        """Standard project domain matching Odoo's project.open_view_project_all action:
        - Filters by allowed companies (or shared projects where company_id = False)
        - Excludes internal projects
        - Excludes project templates
        """
        domain = [
            '|',
            ('company_id', '=', False),
            ('company_id', 'in', request.env.companies.ids),
        ]
        Project = request.env['project.project']
        if 'is_internal_project' in Project._fields:
            domain.append(('is_internal_project', '=', False))
        if 'is_template' in Project._fields:
            domain.append(('is_template', '=', False))
        return domain

    def _get_sale_orders_for_projects(self, projects, analytic_records=None):
        """Helper to get all valid sale orders linked to given projects, their tasks,
        or analytic lines, respecting active company access and permissions.
        """
        if not projects:
            return request.env['sale.order']
        project_records = request.env['project.project'].browse(
            projects.ids if hasattr(projects, 'ids') else projects,
        )
        so_ids = set()
        if 'sale_order_id' in project_records._fields:
            so_ids.update(project_records.sudo().mapped('sale_order_id').ids)
        if 'sale_line_id' in project_records._fields:
            so_ids.update(project_records.sudo().mapped('sale_line_id.order_id').ids)

        tasks = request.env['project.task'].sudo().search_read([
            ('project_id', 'in', project_records.ids),
            '|', ('sale_order_id', '!=', False), ('sale_line_id', '!=', False),
        ], ['sale_order_id', 'sale_line_id'])
        for t in tasks:
            if t.get('sale_order_id'):
                so_ids.add(t['sale_order_id'][0])
        task_sale_line_ids = [t['sale_line_id'][0] for t in tasks if t.get('sale_line_id')]
        if task_sale_line_ids:
            lines = request.env['sale.order.line'].sudo().search_read([
                ('id', 'in', task_sale_line_ids),
            ], ['order_id'])
            for line in lines:
                if line.get('order_id'):
                    so_ids.add(line['order_id'][0])

        if analytic_records:
            if hasattr(analytic_records, 'mapped'):
                if 'order_id' in analytic_records._fields:
                    so_ids.update(analytic_records.sudo().mapped('order_id').ids)
                if 'so_line' in analytic_records._fields:
                    so_ids.update(analytic_records.sudo().mapped('so_line.order_id').ids)

        if not so_ids:
            return request.env['sale.order']
        try:
            return request.env['sale.order'].search([
                ('id', 'in', list(so_ids)),
                '|', ('company_id', '=', False), ('company_id', 'in', request.env.companies.ids),
            ])
        except (AccessError, UserError) as err:
            _logger.debug("Failed to search sale orders: %s", err)
            return request.env['sale.order']

    @http.route('/project/task/count', auth='user', type='jsonrpc')
    def get_project_task_count(self, **kw):
        """Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data for
            the project task graph."""
        self._init_request_context(**kw)
        project_name = []
        total_task = []
        colors = []
        base_domain = self._get_project_domain()
        if request.env.user.has_group('project.group_project_manager'):
            project_ids = request.env['project.project'].search(base_domain)
        else:
            project_ids = request.env['project.project'].search(
                base_domain + [('user_id', '=', request.env.uid)])
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
            'color': colors,
        }

    @http.route('/employee/timesheet', auth='user', type='jsonrpc')
    def get_top_timesheet_employees(self, **kw):
        """Summary:
            when the page is loaded, get the data for the timesheet graph.
        Return:
            type:It is a list. This list contains data that affects the graph
            of employees."""
        self._init_request_context(**kw)
        base_domain = self._get_project_domain()
        if request.env.user.has_group('project.group_project_manager'):
            allowed_projects = request.env['project.project'].search(base_domain)
        else:
            allowed_projects = request.env['project.project'].search(
                base_domain + [('user_id', '=', request.env.uid)])
        if not allowed_projects:
            return [[], []]
        query = '''select hr_employee.name as employee, sum(unit_amount) as unit
                    from account_analytic_line
                    inner join hr_employee on hr_employee.id =
                    account_analytic_line.employee_id
                    where account_analytic_line.project_id in %s
                    group by hr_employee.id, hr_employee.name ORDER
                    BY unit DESC Limit 10 '''
        request.env.cr.execute(query, [tuple(allowed_projects.ids)])
        top_product = request.env.cr.dictfetchall()
        unit = [record.get('unit') for record in top_product]
        employee = [record.get('employee') for record in top_product]
        return [unit, employee]

    @http.route('/project/filter', auth='user', type='jsonrpc')
    def project_filter(self, **kw):
        """Summary:
            transferring data to the selection field that works as a filter
        Returns:
            type:list of lists, it contains the data for the corresponding
            filter."""
        self._init_request_context(**kw)
        project_list = []
        employee_list = []
        base_domain = self._get_project_domain()
        if request.env.user.has_group('project.group_project_manager'):
            project_ids = request.env['project.project'].search(base_domain)
        else:
            project_ids = request.env['project.project'].search(
                base_domain + [('user_id', '=', request.env.uid)])
        employee_ids = request.env['hr.employee'].search([
            '|', ('company_id', '=', False), ('company_id', 'in', request.env.companies.ids),
        ])
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

    @http.route('/project/filter-apply', auth='user', type='jsonrpc')
    def project_filter_apply(self, **kw):
        """Summary:
            transferring data after filter applied
        Args:
            kw(dict):This parameter contains the value of selection field
        Returns:
            type:dict, it contains the data for the corresponding
            filtrated transferring data to ui after filtration."""
        self._init_request_context(**kw)
        data = kw['data']
        base_domain = self._get_project_domain()
        if not request.env.user.has_group('project.group_project_manager'):
            base_domain = base_domain + [('user_id', '=', request.env.uid)]

        # checking the employee selected or not
        if data['employee'] == 'null':
            emp_selected = request.env['hr.employee'].search([
                '|', ('company_id', '=', False), ('company_id', 'in', request.env.companies.ids),
            ]).ids
        else:
            emp_selected = [int(data['employee'])]
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        start_date_val = None
        end_date_val = None
        if start_date and start_date != 'null':
            start_date_val = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date and end_date != 'null':
            end_date_val = dt.datetime.strptime(end_date, "%Y-%m-%d").date()

        if data['project'] == 'null':
            project_domain = list(base_domain)
            if start_date_val:
                project_domain.append(('date_start', '>=', start_date_val))
            if end_date_val:
                project_domain.append(('date_start', '<=', end_date_val))
            pro_selected = request.env['project.project'].search(project_domain).ids
        else:
            pro_selected = [int(data['project'])]

        timesheet_domain = [
            ('project_id', 'in', pro_selected),
            ('employee_id', 'in', emp_selected),
        ]
        if start_date_val:
            timesheet_domain.append(('date', '>=', start_date_val))
        if end_date_val:
            timesheet_domain.append(('date', '<=', end_date_val))

        report_project = request.env['timesheets.analysis.report']
        analytic_project = request.env['account.analytic.line']
        if report_project.has_access('read'):
            report_project = report_project.search(timesheet_domain)
        if analytic_project.has_access('read'):
            analytic_project = analytic_project.search(timesheet_domain)
        margin = round(sum(report_project.mapped('margin')), 2) if report_project else 0
        sale_orders = self._get_sale_orders_for_projects(pro_selected, analytic_records=analytic_project)
        total_time = sum(analytic_project.mapped('unit_amount')) if analytic_project else 0
        return {
            'total_project': pro_selected,
            'total_emp': emp_selected,
            'total_task': request.env['project.task'].search(
                [('project_id', 'in', pro_selected)]).ids,
            'hours_recorded': total_time,
            'list_hours_recorded': analytic_project.ids,
            'total_margin': margin,
            'total_margin_ids': report_project.ids,
            'total_so': sale_orders.ids,
        }

    @http.route('/get/tiles/data', auth='user', type='jsonrpc')
    def get_tiles_data(self, **kw):
        """Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data that
             affects the dashboard view."""
        self._init_request_context(**kw)
        base_domain = self._get_project_domain()
        if request.env.user.has_group('project.group_project_manager'):
            all_project = request.env['project.project'].search(base_domain)
            all_task = request.env['project.task'].search([
                ('project_id', 'in', all_project.ids),
            ])
            analytic_project = request.env['account.analytic.line'].search([
                ('project_id', 'in', all_project.ids),
            ])
            report_project = request.env['timesheets.analysis.report'].search([
                ('project_id', 'in', all_project.ids),
            ])
            margin = round(sum(report_project.mapped('margin')), 2) if report_project else 0
            total_time = sum(analytic_project.mapped('unit_amount'))
            employees = request.env['hr.employee'].search([
                '|', ('company_id', '=', False), ('company_id', 'in', request.env.companies.ids),
            ])
            sale_orders = self._get_sale_orders_for_projects(all_project, analytic_records=analytic_project)
            project_stage_ids = request.env['project.project.stage'].sudo().search([])
            project_stage_list = []
            for project_stage_id in project_stage_ids:
                total_projects = request.env[
                    'project.project'].sudo().search_count(
                    base_domain + [('stage_id', '=', project_stage_id.id)])
                project_stage_list.append({'id': project_stage_id.id, 'name': project_stage_id.name,
                                           'projects': total_projects})
            return {
                'total_projects': len(all_project),
                'total_projects_ids': all_project.ids,
                'total_tasks': len(all_task),
                'total_tasks_ids': all_task.ids,
                'total_hours': total_time,
                'total_hours_ids': analytic_project.ids,
                'total_profitability': margin,
                'total_margin_ids': report_project.ids,
                'total_employees': len(employees),
                'total_employees_ids': employees.ids,
                'total_sale_orders': len(sale_orders),
                'sale_orders_ids': sale_orders.ids,
                'project_stage_list': project_stage_list,
                'project_kanban_view_id': request.env.ref('project.view_project_kanban', raise_if_not_found=False).id if request.env.ref('project.view_project_kanban', raise_if_not_found=False) else False,
                'currency_symbol': request.env.company.currency_id.symbol or '$',
                'flag': 1}
        all_project = request.env['project.project'].search(
            base_domain + [('user_id', '=', request.env.uid)])
        all_task = request.env['project.task'].search([
            ('project_id', 'in', all_project.ids),
            ('user_ids', 'in', [request.env.uid]),
        ])
        analytic_project = request.env['account.analytic.line']
        report_project = request.env['timesheets.analysis.report']
        if analytic_project.has_access('read'):
            analytic_project = analytic_project.search(
                [('project_id', 'in', all_project.ids)],
            )
        total_time = sum(analytic_project.mapped('unit_amount')) if analytic_project else 0
        if report_project.has_access('read'):
            report_project = report_project.search([
                ('project_id', 'in', all_project.ids),
            ])
        margin = round(sum(report_project.mapped('margin')), 2) if report_project else 0
        sale_orders = self._get_sale_orders_for_projects(all_project, analytic_records=analytic_project)
        project_stage_ids = request.env['project.project.stage'].sudo().search([])
        project_stage_list = []
        for project_stage_id in project_stage_ids:
            total_projects = request.env['project.project'].sudo().search_count(
                base_domain + [('stage_id', '=', project_stage_id.id),
                               ('id', 'in', all_project.ids)])
            project_stage_list.append({
                'id': project_stage_id.id,
                'name': project_stage_id.name,
                'projects': total_projects,
            })
        return {
            'total_projects': len(all_project),
            'total_projects_ids': all_project.ids,
            'total_tasks': len(all_task),
            'total_tasks_ids': all_task.ids,
            'total_hours': total_time,
            'total_hours_ids': analytic_project.ids,
            'total_profitability': margin,
            'total_margin_ids': report_project.ids,
            'total_employees': 0,
            'total_employees_ids': [],
            'total_sale_orders': len(sale_orders),
            'sale_orders_ids': sale_orders.ids,
            'project_stage_list': project_stage_list,
            'project_kanban_view_id': request.env.ref('project.view_project_kanban', raise_if_not_found=False).id if request.env.ref('project.view_project_kanban', raise_if_not_found=False) else False,
            'currency_symbol': request.env.company.currency_id.symbol or '$',
            'flag': 2}

    @http.route('/get/hours', auth='user', type='jsonrpc')
    def get_hours_data(self, **kw):
        """Summary:
            when the page is loaded get the data for the hour table.
        Return:
            type:It is a dictionary variable. This dictionary contains data that
            hours table."""
        self._init_request_context(**kw)
        base_domain = self._get_project_domain()
        if request.env.user.has_group('project.group_project_manager'):
            all_project = request.env['project.project'].search(base_domain).ids
        else:
            all_project = request.env['project.project'].search(
                base_domain + [('user_id', '=', request.env.uid)]).ids
        report_records = request.env['timesheets.analysis.report']
        if report_records.has_access('read'):
            report_records = report_records.search([
                ('project_id', 'in', all_project),
            ])

        hour_recorded = [sum(report_records.filtered(lambda x: x.billable_type == '09_non_billable').mapped('unit_amount'))]
        hour_recorde = [sum(report_records.filtered(lambda x: x.billable_type == '04_billable_time').mapped('unit_amount'))]
        billable_fix = [sum(report_records.filtered(lambda x: x.billable_type in ('02_billable_fixed', '06_billable_milestones', '08_billable_manual')).mapped('unit_amount'))]
        non_billable = hour_recorded
        total_hr = [sum(report_records.mapped('unit_amount'))]

        return {
            'hour_recorded': hour_recorded,
            'hour_recorde': hour_recorde,
            'billable_fix': billable_fix,
            'non_billable': non_billable,
            'total_hr': total_hr,
        }

    @http.route('/get/task/data', auth='user', type='jsonrpc')
    def get_task_data(self, **kw):
        """
        Summary:
            when the page is loaded, get the data from different models and
            transfer to the js file.
            Return a dictionary variable.
        Return:
            type:It is a dictionary variable. This dictionary contains data
            that affecting project task table."""
        self._init_request_context(**kw)
        base_domain = self._get_project_domain()
        if request.env.user.has_group('project.group_project_manager'):
            all_project = request.env['project.project'].search(base_domain)
            tasks = request.env['project.task'].search([
                ('project_id', 'in', all_project.ids),
            ], order='project_id asc')
            project_name = []
            for task in tasks:
                stage_name = task.stage_id.name if task.stage_id else ''
                project_name.append([task.name, task.id, task.project_id.name, stage_name])
            return {
                'project': project_name,
            }
        all_project = request.env['project.project'].search(
            base_domain + [('user_id', '=', request.env.uid)]).ids
        all_tasks = request.env['project.task'].search([
            ('project_id', 'in', all_project),
        ])
        task_project = []
        for task in all_tasks:
            stage_name = task.stage_id.name if task.stage_id else ''
            task_project.append([task.name, task.id, task.project_id.name, stage_name])
        return {
            'project': task_project,
        }
