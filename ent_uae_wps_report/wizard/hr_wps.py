# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Harshitha AP (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
import io
import json
import pytz
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo import api, fields, models
from odoo.tools import _
from odoo.tools import json_default

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class HrWps(models.TransientModel):
    """Wizard hr wps to filter xlsx report """
    _name = 'hr.wps'
    _description = "HR WPS Wizard"

    report_file = fields.Char(string='Report File', help='to set report file')
    name = fields.Char(string="File Name")
    start_date = fields.Date(string='Start Date', required=True,
                             help="to add start date for filtering")
    end_date = fields.Date(string="End Date", required=True,
                           help="to add end date for filtering")
    days = fields.Integer(string="Days of Payment", readonly=True, store=True,
                          help="to set days of payment")
    salary_month = fields.Selection([('01', 'January'),
                                     ('02', 'February'),
                                     ('03', 'March'),
                                     ('04', 'April'),
                                     ('05', 'May'),
                                     ('06', 'June'),
                                     ('07', 'July'),
                                     ('08', 'August'),
                                     ('09', 'September'),
                                     ('10', 'October'),
                                     ('11', 'November'),
                                     ('12', 'December')
                                     ], string="Month of Salary", readonly=True,
                                    help="to set salary month")

    @api.onchange('start_date', 'end_date')
    def _onchange_date(self):
        """Used to change the days and salary month"""
        if self.start_date and self.end_date:
            start = str(self.start_date).split('-')
            end = str(self.end_date).split('-')
            self.days = 1 + (date(year=int(end[0]), month=int(end[1]),
                                  day=int(end[2]))
                             - date(year=int(start[0]), month=int(start[1]),
                                    day=int(start[2]))).days
            if start[1] == end[1]:
                self.salary_month = start[1]

    def action_print_xlsx(self):
        """Used to print xlsx report"""
        company = self.env.company
        if not company.company_registry:
            raise UserError(_('Please Set Company Registry Number First'))
        slips_to_validate = self.env['hr.payslip'].search([
            ('date_from', '>=', self.start_date),
            ('date_to', '<=', self.end_date),
            ('state', 'in', ['done', 'paid']),
        ])
        users = slips_to_validate.mapped('employee_id')
        missing_labour = users.filtered(lambda e: not e.labour_card_number)
        missing_salary = users.filtered(lambda e: not e.salary_card_number)
        missing_agent = users.filtered(lambda e: not e.agent_id)
        if missing_labour:
            raise UserError(_('Please Set Labour Card Number for: %s') %
                            ', '.join(missing_labour.mapped('name')))
        if missing_salary:
            raise UserError(_('Please Set Salary Card Number / Account Number for: %s') %
                            ', '.join(missing_salary.mapped('name')))
        if missing_agent:
            raise UserError(_('Please Set Agent/Bank for: %s') %
                            ', '.join(missing_agent.mapped('name')))
        if not self.env['res.users'].browse(self.env.uid).tz:
            raise UserError(_('Please Set a User Timezone'))
        if self.start_date and self.end_date:
            start = str(self.start_date).split('-')
            end = str(self.end_date).split('-')
            if not start[1] == end[1]:
                raise UserError(_('The Dates Can of Same Month Only'))
        slips = self.get_data(self.start_date, self.end_date)
        if not slips:
            raise UserError(_('There are no payslip Created for the selected '
                              'month'))
        company = self.env.company
        user = self.env['res.users'].browse(self.env.uid)
        if user.tz:
            t_z = pytz.timezone(user.tz) or pytz.utc
            c_date = pytz.utc.localize(datetime.now()).astimezone(t_z)
            time = pytz.utc.localize(datetime.now()).astimezone(t_z)
        else:
            c_date = datetime.now()
            time = datetime.now()
        if not company.employer_id:
            raise UserError(_('Configure Your Company Employer ID'))
        self.name = company.employer_id + c_date.strftime("%y%m%d%H%M%S")
        self.report_file = company.employer_id + c_date.strftime("%y%m%d%H%M%S")
        if not company.bank_ids:
            raise UserError(_('Configure Your Bank In Accounting Dashboard'))
        datas = {
            'context': self._context,
            'date': c_date,
            'time': time,
            'start_date': self.start_date,
            'end_date': self.end_date,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'hr.wps',
                     'options': json.dumps(datas,
                                           default=json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Uae wps Report'
                     },
            'report_type': 'wps_xlsx'
        }

    def get_data(self, start, end):
        """This function is used to fetch data"""
        cur = self._cr
        slips_ids = self.env['hr.payslip'].search([
            ('date_from', '>=', start),
            ('date_to', '<=', end),
            ('state', 'in', ['done', 'paid']),
        ]).sorted('id')
        if not slips_ids:
            return False
        emp_ids = []
        for rec in slips_ids:
            if rec.employee_id.id in emp_ids:
                slips_ids -= rec
            else:
                emp_ids.append(rec.employee_id.id)

        if len(slips_ids) == 1:
            query = """select hr_employee.id, labour_card_number,
            salary_card_number, agent_id, hr_payslip_line.amount,
            hr_payslip_line.slip_id from hr_employee join hr_payslip_line on
            hr_employee.id = hr_payslip_line.employee_id where
            hr_payslip_line.code = 'NET' and hr_payslip_line.slip_id = """ \
                    + str(slips_ids.id) + """ """
        else:
            slips_ids = str(tuple(slips_ids.mapped('id')))
            query = """select hr_employee.id, labour_card_number,
            salary_card_number, agent_id, hr_payslip_line.amount,
            hr_payslip_line.slip_id from hr_employee join hr_payslip_line on
            hr_employee.id = hr_payslip_line.employee_id where
            hr_payslip_line.code = 'NET' and hr_payslip_line.slip_id in """ \
                    + slips_ids + """ """
        cur.execute(query)
        data = cur.fetchall()
        return data

    def get_days(self, slip_id):
        """This fn is used to get worked days"""
        days = self.env['hr.payslip.worked_days'].search([('payslip_id', '=',
                                                           slip_id)])
        total_days = sum(rec.number_of_days for rec in days)

        return total_days

    def get_leaves(self, emp_id, start, end):
        """This function is used to get leave"""
        leaves = self.env['hr.leave'].search(['&',
                                              ('employee_id', '=', emp_id),
                                              ('date_from', '>=', start),
                                              ('date_to', '<=', end),
                                              ('holiday_status_id', '=',
                                               4)]).number_of_days
        return leaves * -1

    def get_xlsx_report(self, lines, response):
        """Write the values in to the xlsx sheet which fetched using query"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        format0 = workbook.add_format({'font_size': 10, 'align': 'center',
                                       'bold': False})
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True})
        sheet = workbook.add_worksheet('SIF Report')
        dat = self.get_data(lines['start_date'], lines['end_date'])
        if dat == 11:
            raise UserError(_('There is no payslips created for this month'))
        dat = [list(data) for data in dat]
        for data in dat:
            bank = self.env['res.bank'].browse(data[3])
            data[3] = bank.routing_code or ''
        count = 0
        v_sum = 0
        sheet.set_column(0, 0, 6)
        sheet.set_column(1, 1, 16)
        sheet.set_column(2, 2, 16)
        sheet.set_column(3, 3, 16)
        sheet.set_column(4, 4, 12)
        sheet.set_column(5, 5, 12)
        sheet.set_column(6, 6, 14)
        sheet.set_column(7, 7, 12)
        sheet.set_column(8, 8, 10)
        sheet.set_column(9, 9, 8)
        sheet.write(count, 0, '', format1)
        sheet.write(count, 1, 'Labour Card Number', format1)
        sheet.write(count, 2, 'Agent ID (Routing Code)', format1)
        sheet.write(count, 3, 'Salary Card Number', format1)
        sheet.write(count, 4, 'Start Date', format1)
        sheet.write(count, 5, 'End Date', format1)
        sheet.write(count, 6, 'Working Days', format1)
        sheet.write(count, 7, 'Amount', format1)
        sheet.write(count, 8, 'Currency', format1)
        sheet.write(count, 9, 'Leaves', format1)
        for count in enumerate(dat):
            days = self.get_days(count[1][5])
            leaves = self.get_leaves(count[1][0], lines['start_date'],
                                     lines['end_date'])
            sheet.write(count[0] + 1, 0, 'EDR', format0)
            sheet.write(count[0] + 1, 1, count[1][1] or '', format0)
            sheet.write(count[0] + 1, 2, count[1][3] or '', format0)
            sheet.write(count[0] + 1, 3, count[1][2] or '', format0)
            sheet.write(count[0] + 1, 4, str(lines['start_date']), format0)
            sheet.write(count[0] + 1, 5, str(lines['end_date']), format0)
            sheet.write(count[0] + 1, 6, str(int(days)).zfill(4), format0)
            v_sum += int(count[1][4])
            sheet.write(count[0] + 1, 7, count[1][4], format0)
            sheet.write(count[0] + 1, 8, 'AED', format0)
            sheet.write(count[0] + 1, 9, leaves, format0)
        count = count[0] + 2
        company = self.env.company
        sheet.set_column(1, 1, 14)
        sheet.set_column(2, 2, 12)
        sheet.set_column(3, 3, 16)
        sheet.set_column(4, 4, 9)
        sheet.set_column(5, 5, 9)
        routing_code = company.bank_ids[:1].bank_id.routing_code or ''
        date_str = str(lines['date']).split(' ')[0]
        time_parts = str(lines['date']).split(' ')[1].split(':')
        time_str = time_parts[0] + time_parts[1]
        month_year = str(lines['end_date']).split('-')
        month_year = str(month_year[1]) + str(month_year[0])
        emp_count = count - 1
        sheet.write(count, 0, 'SCR', format0)
        sheet.write(count, 1, company.company_registry or '', format0)
        sheet.write(count, 2, routing_code, format0)
        sheet.write(count, 3, date_str, format0)
        sheet.write(count, 4, time_str, format0)
        sheet.write(count, 5, month_year, format0)
        sheet.write(count, 6, emp_count, format0)
        sheet.write(count, 7, v_sum, format0)
        sheet.write(count, 8, 'AED', format0)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()