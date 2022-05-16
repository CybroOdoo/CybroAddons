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


import json
import io
import calendar
from datetime import timedelta, datetime
from dateutil import rrule

from reportlab.platypus.tableofcontents import delta
from xlsxwriter import workbook

from odoo.tools import date_utils
from odoo import fields, models,_
from calendar import monthrange
from odoo.exceptions import UserError, ValidationError

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class SaleReportAdvance(models.TransientModel):
    _name = "sale.report.weekly"

    date = fields.Date(string='Date', required=True)
    invoice_status = fields.Selection(
        [('invoiced', 'Fully Invoiced'),
         ('to invoice', 'To Invoice'),
         ('no', 'Nothing to Invoice')],
        string='Invoice Status', default='no', required=True)
    amount_type = fields.Selection(
        [('total', 'Total Amount'), ('untax', 'Untaxed Amount')],
        string='Total Amount', default='total')
    today_date = fields.Date(default=fields.Date.today())

    def get_weekly_report(self):
        datas = self._get_data()
        return self.env.ref('sale_report_advanced.action_sales_weekly').report_action([], data=datas)

    def _get_data(self):
        result = []
        times=[{'id':'morning','name':'Morning (5:00-12:00)'}, {'id':'noon','name':'Noon (1:00-17:00)'},{'id':'evening','name':'Evening (18:00-23:00)'}]
        if self.invoice_status == 'invoiced':
            sale_order = self.env['sale.order'].sudo().search([('invoice_status', '=', self.invoice_status),('date_order','>',self.date),('state','!=','cancel')])
        elif self.invoice_status == 'to invoice':
            sale_order = self.env['sale.order'].sudo().search([('invoice_status', '=', self.invoice_status),('date_order','>',self.date),('state','!=','cancel')])
        else:
            sale_order = self.env['sale.order'].sudo().search([('invoice_status', '=', self.invoice_status),('date_order','>',self.date),('state','!=','cancel')])
        for rec in sale_order:
            if self.amount_type=='total':
                if rec.date_order.hour > 5 and rec.date_order.hour <=12:
                    res = {
                        'order': rec.name,
                        'amount':rec.amount_total ,
                        'time':'morning',
                        'date':rec.date_order.date()
                    }
                    result.append(res)

                if rec.date_order.hour > 12 and rec.date_order.hour <=17:
                    res = {
                        'order': rec.name,
                        'amount': rec.amount_total,
                        'time': 'noon',
                        'date': rec.date_order.date()

                    }
                    result.append(res)

                if rec.date_order.hour > 17 and rec.date_order.hour <=23:
                    res = {
                        'order': rec.name,
                        'amount': rec.amount_total,
                        'time': 'evening',
                        'date': rec.date_order.date()

                    }
                    result.append(res)
            else:
                if rec.date_order.hour > 5 and rec.date_order.hour <= 12:
                    res = {
                        'order':rec.name,
                        'amount':rec.amount_untaxed,
                        'time':'morning',
                        'date': rec.date_order.date()

                    }
                    result.append(res)

                if rec.date_order.hour > 12 and rec.date_order.hour <= 17:
                    res = {
                        'order': rec.name,
                        'amount': rec.amount_untaxed,
                        'time': 'noon',
                        'date': rec.date_order.date()

                    }
                    result.append(res)

                if rec.date_order.hour > 17 and rec.date_order.hour <= 23:
                    res = {
                        'order': rec.name,
                        'amount': rec.amount_untaxed,
                        'time': 'evening',
                        'date': rec.date_order.date()

                    }
                    result.append(res)
        datas = {
                'ids': self,
                'model': 'sale.report.weekly',
                'form': result,
                'date': self.date,
                'type':self.amount_type,
                'times':times

            }
        return datas

    def get_excel_weekly_report(self):
        datas = self._get_data()
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'sale.report.weekly',
                     'output_format': 'xlsx',
                     'options': json.dumps(datas, default=date_utils.json_default),
                     'report_name': 'Excel Report Name',
                     },
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True, 'font_size': '20px'})
        sheet.merge_range('G2:I3', 'Hourly Sales Report', head)
        format1 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bg_color': '#f5f9ff', 'border': 1})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,
             'bg_color': '#6BA6FE', 'border': 1})
        format3 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True,'bg_color':'#95ff63','border': 1})
        format4 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'border': 1})
        h_row = 7
        h_col = 7
        count = 0
        row = 4
        row_number = 5
        for rec in data['times']:
            col = 6
            row = row + count + 4
            sheet.merge_range(h_row,h_col-1,h_row,h_col+1,rec['name'] , format3)
            sheet.write(row, col, 'Order', format2)
            sheet.set_column(row, col, 15)
            col += 1
            sheet.write(row, col, 'Date', format2)
            sheet.set_column(row, col, 15)
            col += 1
            if data['type'] =='total':
                sheet.write(row, col, 'Total', format2)
                sheet.set_column(row, col, 15)
                col += 1
            else:
                sheet.write(row, col, 'Untaxed Total', format2)
                sheet.set_column(row, col, 15)
                col += 1
            t_total = 0

            row_number = row_number +4
            count=0
            t_col = 7
            for val in data['form']:
                if val['time'] == rec['id']:
                    count += 1
                    column_number = 6
                    sheet.write(row_number, column_number, val['order'], format1)
                    sheet.set_column(row_number, column_number, 15)
                    column_number += 1
                    sheet.write(row_number, column_number, val['date'], format1)
                    sheet.set_column(row_number, column_number, 15)
                    column_number += 1
                    sheet.write(row_number, column_number, val['amount'], format1)
                    t_total += val['amount']
                    sheet.set_column(row_number, column_number, 15)
                    row_number+=1
            sheet.write(row_number, t_col, 'Total', format4)
            sheet.set_column(row_number, t_col, 15)
            t_col += 1
            sheet.write(row_number, t_col, t_total, format4)
            h_row= h_row+ count+4
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
