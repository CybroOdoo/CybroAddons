# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields
import datetime
from odoo.exceptions import except_orm
from dateutil.relativedelta import relativedelta
try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    class ReportXlsx(object):
        def __init__(self, *args, **kwargs):
            pass


class ProjectReportXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        sheet1 = "Project plan"
        sheet2 = "Notes"
        worksheet1 = workbook.add_worksheet(sheet1)
        worksheet2 = workbook.add_worksheet(sheet2)
        format_main_header = workbook.add_format({'font_size': 14, 'bg_color': 'silver', 'bold': 1, 'border': 1,
                                                  'align': 'center', 'valign': 'vcenter'})
        format_header = workbook.add_format({'bold': 1, 'border': 1, 'align': 'center',
                                             'valign': 'vcenter', 'bg_color': 'silver'})
        header = workbook.add_format({'bold': 1, 'border': 1, 'align': 'center',
                                      'valign': 'vcenter', 'bg_color': 'silver'})
        left_header = workbook.add_format({'bold': 1, 'border': 1, 'align': 'center',
                                           'valign': 'vcenter'})
        format_cell = workbook.add_format({'border': 1, 'align': 'center'})

        # ---------------------Project details-------------------------- #

        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        tasks = self.env['project.task'].search([])
        if date_from and not date_to:
            task = tasks.search([('date_start', '>=', date_from), ('project_id', '=', objects.name)])
        elif date_to and not date_from:
            task = tasks.search([('date_start', '<=', date_to), ('project_id', '=', objects.name)])
        elif date_from and date_to:
            task = tasks.search([('date_start', '<=', date_to), ('date_start', '>=', date_from),
                                 ('project_id', '=', objects.name)])
        else:
            task = tasks.search([('project_id', '=', objects.name)])

        report_date = datetime.datetime.now().strftime("%m/%d/%Y")
        completed = effective_hours = planned_hours = 0
        for data in task:
            if data.effective_hours:
                effective_hours += data.effective_hours
            if data.planned_hours:
                planned_hours += data.planned_hours
            if planned_hours != 0:
                completed = str(int((effective_hours * 100) / planned_hours))
        row = col = 0
        worksheet1.merge_range(row, col, row + 1, col + 25, "Project Plan", format_main_header)
        row += 4
        worksheet1.merge_range(row, col, row, col + 6, self.env.user.company_id.name, left_header)
        row += 2
        worksheet1.merge_range(row, col, row, col + 2, "Project Name", left_header)
        col += 3
        worksheet1.merge_range(row, col, row, col + 3, objects.name, format_cell)
        col = 0
        row += 1
        worksheet1.merge_range(row, col, row, col + 2, "Report Date", left_header)
        col += 3
        worksheet1.merge_range(row, col, row, col + 3, report_date, format_cell)
        col = 0
        row += 1
        worksheet1.merge_range(row, col, row, col + 2, "Completed", left_header)
        col += 3
        worksheet1.merge_range(row, col, row, col + 3, str(completed) + " %", format_cell)
        row += 1

        if task:

            # ---------------------Pie chart for overall task status-------------------------- #
            stage_obj = self.env['project.task.type'].search([])
            stages_all = {}
            for obj in stage_obj:
                stages_all[obj.name] = 0
            for data in task:
                stages_all[data.stage_id.name] += 1
            stages = stages_all.keys()
            count = stages_all.values()
            percentage = []
            total = sum(count)
            for item in range(len(count)):
                percentage.append((float(count[item]) / total) * 100)
            row = 0
            col = 0
            worksheet2.merge_range(row, col, row + 1, col + 3, "Percentage of Task complete", header)
            row += 2
            for item in range(len(stages)):
                worksheet2.merge_range(row, col, row, col + 1, stages[item], format_cell)
                col += 2
                worksheet2.merge_range(row, col, row, col + 1, int(percentage[item]), format_cell)
                col = 0
                row += 1
            chart_pie = workbook.add_chart({'type': 'pie'})
            chart_pie.add_series({
                'categories': '=' + sheet2 + '!$A$3:$A$10',
                'values': '=' + sheet2 + '!$C$3:$C$10',
                'points': [],
            })
            chart_pie.set_title({'name': 'Overall Task Status'})
            worksheet1.insert_chart('A13', chart_pie)

            # # ---------------------Bar chart for Time duration-------------------------- #
            chart_bar_t = workbook.add_chart({'type': 'bar'})
            actual_time = planned_time = 0
            for data in task:
                if data.planned_hours:
                    planned_time += data.planned_hours
                actual_time += data.effective_hours
            data_bar_t = [
                ['Planned time', 'Actual time'],
                [planned_time, actual_time],
            ]
            col = 6
            row = 0
            worksheet2.merge_range(row, col, row + 1, col + 3, "Time Duration(Hours)", header)
            row += 2
            for item in range(2):
                worksheet2.merge_range(row, col, row, col + 1, data_bar_t[0][item], format_cell)
                col += 2
                worksheet2.merge_range(row, col, row, col + 1, data_bar_t[1][item], format_cell)
                col = 6
                row += 1
            chart_bar_t.add_series({'name': 'Time',
                                    'categories': '=' + sheet2 + '!$G$3:$G$4',
                                    'values': '=' + sheet2 + '!$I$3:$I$4',
                                    })
            chart_bar_t.set_title({'name': 'Time Duration'})
            worksheet1.insert_chart('I13', chart_bar_t)

            # # ---------------------Bar chart for Budget-------------------------- #
            chart_bar_b = workbook.add_chart({'type': 'bar'})
            actual_amount = planned_amount = 0
            if objects.planned_amount:
                planned_amount = objects.planned_amount
            account_obj = self.env['account.analytic.line'].search([])
            for acc in account_obj:
                if acc.account_id == objects.analytic_account_id:
                    actual_amount += acc.amount
            data_bar_b = [
                ['Planned', 'Actual'],
                [planned_amount, abs(actual_amount)],
            ]
            col = 6
            row = 6
            worksheet2.merge_range(row, col, row + 1, col + 3, "Budget", header)
            row += 2
            for item in range(2):
                worksheet2.merge_range(row, col, row, col + 1, data_bar_b[0][item], format_cell)
                col += 2
                worksheet2.merge_range(row, col, row, col + 1, data_bar_b[1][item], format_cell)
                col = 6
                row += 1
            chart_bar_b.add_series({'name': 'Amount',
                                    'categories': '=' + sheet2 + '!$G$9:$G$10',
                                    'values': '=' + sheet2 + '!$I$9:$I$10',
                                    })
            chart_bar_b.set_title({'name': 'Budget'})
            worksheet1.insert_chart('Q13', chart_bar_b)

            # # ---------------------Task description table 1 -------------------------- #
            row = 31
            col = 0
            worksheet1.merge_range(row, col, row, col + 3, "Task", format_header)
            col += 4
            worksheet1.merge_range(row, col, row, col + 1, "Assigned to", format_header)
            col += 2
            worksheet1.write(row, col, "Priority", format_header)
            col += 1
            worksheet1.merge_range(row, col, row, col + 1, "Status", format_header)
            col += 2
            row += 1
            for data in task:
                assigned_to = "-"
                if data.user_id.name:
                    assigned_to = data.user_id.name
                col = 0
                worksheet1.merge_range(row, col, row, col + 3, data.name, format_cell)
                col += 4
                worksheet1.merge_range(row, col, row, col + 1, assigned_to, format_cell)
                col += 2
                priority = ""
                for i in range(int(data.priority)):
                    priority += "*"
                worksheet1.write(row, col, priority, format_cell)
                col += 1
                worksheet1.merge_range(row, col, row, col + 1, data.stage_id.name, format_cell)
                row += 1

            # ---------------------Task description table 2 -------------------------- #
            row = 14
            col = 0
            worksheet2.merge_range(row, col, row, col + 3, "Task", format_header)
            col += 4
            worksheet2.merge_range(row, col, row, col + 1, "Assigned to", format_header)
            col += 2
            worksheet2.merge_range(row, col, row, col + 1, "Start", format_header)
            col += 2
            worksheet2.merge_range(row, col, row, col + 1, "End", format_header)
            col += 2
            worksheet2.write(row, col, "Days", format_header)
            col += 1
            worksheet2.merge_range(row, col, row, col + 1, "Status", format_header)
            row += 1
            col = 0
            for data in task:
                start_date = fields.Datetime.from_string(data.date_start)
                start_date1 = start_date.strftime("%m-%d-%Y")
                if data.date_end and data.date_end > data.date_start:
                    end_date = fields.Datetime.from_string(data.date_end)
                    date_difference = relativedelta(end_date, start_date).days
                    end_date1 = end_date.strftime("%m-%d-%Y")
                else:
                    date_difference = "-"
                    end_date1 = "-"
                assigned_to = "-"
                if data.user_id.name:
                    assigned_to = data.user_id.name
                worksheet2.merge_range(row, col, row, col + 3, data.name, format_cell)
                col += 4
                worksheet2.merge_range(row, col, row, col + 1, assigned_to, format_cell)
                col += 2
                worksheet2.merge_range(row, col, row, col + 1, start_date1, format_cell)
                col += 2
                worksheet2.merge_range(row, col, row, col + 1, end_date1, format_cell)
                col += 2
                worksheet2.write(row, col, date_difference, format_cell)
                col += 1
                worksheet2.merge_range(row, col, row, col + 1, data.stage_id.name, format_cell)
                col = 0
                row += 1

            # ---------------------Gantt chart view-------------------------- #
            worksheet3 = workbook.add_worksheet()
            if objects.date_start:
                project_start = datetime.datetime.date(fields.Datetime.from_string(objects.date_start))
            else:
                project_start = datetime.datetime.date(fields.Datetime.from_string(objects.create_date))
            start_list = []
            days_list = []
            task_list = []
            task_item = 0
            project_end = datetime.datetime.date(datetime.datetime.now())
            for data in task:
                if data.date_deadline:
                    date_end_fmt = datetime.datetime.date(fields.Datetime.from_string(data.date_deadline))
                    if date_end_fmt > project_end:
                        project_end = date_end_fmt
                else:
                    project_end = project_end + datetime.timedelta(days=30)
                task_item += 1
                start_date = fields.Datetime.from_string(data.date_start)
                start_date1 = datetime.datetime.date(start_date)
                if data.date_end and data.date_end > data.date_start:
                    end_date = fields.Datetime.from_string(data.date_end)
                else:
                    end_date = datetime.datetime.today()
                days = relativedelta(end_date, start_date).days
                task_list.append(data.name)
                start_list.append(start_date1)
                days_list.append(days)
            headings = ['Number', 'Start date', 'Days']
            data = [
                task_list,
                start_list,
                days_list,
            ]
            worksheet3.write_row('A1', headings)
            worksheet3.write_column('A2', data[0])
            worksheet3.write_column('B2', data[1])
            worksheet3.write_column('C2', data[2])
            chart2 = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
            start = 2
            end = start + task_item - 1
            chart2.add_series({
                'name': '=Sheet3!$B$1',
                'categories': '=Sheet3!$A$' + str(start) + ':$A$' + str(end),
                'fill': {'none': True},
                'values': '=Sheet3!$B$' + str(start) + ':$B$' + str(end),
            })
            chart2.add_series({
                'name': '=Sheet3!$C$1',
                'categories': '=Sheet3!$A$' + str(start) + ':$A$' + str(end),
                'fill': {'color': '#4E73B7'},
                'values': '=Sheet3!$C$' + str(start) + ':$C$' + str(end),
            })
            chart2.set_title({'none': True})
            chart2.set_x_axis({'date_axis': True, 'min': project_start, 'max': project_end,
                               'minor_unit': 2, 'minor_unit_type': 'days', 'major_unit': 1,
                               'major_unit_type': 'days', 'num_format': 'dd/mm/yyyy'})
            chart2.set_y_axis({'none': True})
            chart2.set_legend({'none': True})
            worksheet1.insert_chart('K31', chart2, {'x_scale': 2, 'y_scale': 1})
            worksheet3.hide()

        else:
            raise except_orm('Warning', 'No task to display')


ProjectReportXlsx('report.project_status_level_report', 'project.project')
