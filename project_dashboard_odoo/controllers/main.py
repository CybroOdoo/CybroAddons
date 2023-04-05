# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import datetime

from odoo import http
from odoo.http import request


class ProjectFilter(http.Controller):
    """
    The ProjectFilter class provides the filter option to the js.
    When applying the filter return the corresponding data.
        Methods:
            project_filter(self):
                when the page is loaded adding filter options to the selection
                field.
                return a list variable.
            project_filter_apply(self,**kw):
                after applying the filter receiving the values and return the
                filtered data.

    """

    @http.route('/project/filter', auth='public', type='json')
    def project_filter(self):
        """

        Summery:
            transferring data to the selection field that works as a filter
        Returns:
            type:list of lists , it contains the data for the corresponding
            filter.


        """
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
        """
        Summery:
            transferring data after filter 9is applied
        Args:
            kw(dict):This parameter contain value of selection field
        Returns:
            type:dict, it contains the data for the corresponding
            filter.

        and transferring data to ui after filtration.


        """
        data = kw['data']
        pro_selected = []
        emp_selected = []
        # checking tje employee selected or not
        if data['employee'] == 'null':
            emp_selected = [employee.id for employee in
                            request.env['hr.employee'].search([])]
        else:
            emp_selected = [int(data['employee'])]
        start_date = data['start_date']
        end_date = data['end_date']
        pro_selected = False
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
        report_project = request.env['project.profitability.report'].search(
            [('project_id', 'in', pro_selected)])
        to_invoice = sum(report_project.mapped('amount_untaxed_to_invoice'))
        invoice = sum(report_project.mapped('amount_untaxed_invoiced'))
        timesheet_cost = sum(report_project.mapped('timesheet_cost'))
        other_cost = sum(report_project.mapped('expense_cost'))
        profitability = to_invoice + invoice + timesheet_cost + other_cost
        analytic_project = request.env['account.analytic.line'].search(
            [('project_id', 'in', pro_selected),
             ('employee_id', 'in', emp_selected)])
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
            'total_margin': profitability,
            'total_so': sale_orders
        }
