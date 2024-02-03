# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
################################################################################
import json
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import date_utils, io, xlsxwriter



class EventManagementReport(models.TransientModel):
    """Class for Event Management Report"""
    _name = 'event.management.report'
    _description = 'Event Management Report'

    date_from = fields.Date(string="From", help='From a date')
    date_to = fields.Date(string="To", help='To a date')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='Customer of event')
    type_event_ids = fields.Many2many('event.management.type',
                                      'event_type_rel',
                                      'report_id', 'type_id',
                                      string="Type",
                                      help='Event management types')
    event_state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'),
         ('invoice', 'Invoiced'), ('close', 'Close'), ('cancel', 'Canceled')],
        string="State", help='State of event')

    def action_print_pdf_report(self):
        """Method for printing pdf report"""
        data = {
            'model': 'event.management.report',
            'form': self.read()[0],
            'event_types': self.type_event_ids.ids
        }
        return (self.env.ref(
            'event_management.action_report_event_management_report')
                .report_action(self, data=data))

    def action_print_xls_report(self):
        """Method of button for printing xlsx report"""
        rec = self.env.user.sudo().company_id
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError(_('From Date must be less than To Date'))
        data = {
            'event_type': self.type_event_ids.ids,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'customer': self.partner_id.id,
            'state': self.event_state,
            'today_date': fields.datetime.now(),
            'company': [rec.partner_id.name, rec.street, rec.favicon]
        }
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'data': {'model': 'event.management.report',
                     'output_format': 'xlsx',
                     'options': json.dumps(data,
                                           default=date_utils.json_default),
                     'report_name': 'Event Management Report', },
        }

    def get_xlsx_report(self, data, response):
        """Method for fetching data and printing xlsx report from controller"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center',
                                    'bold': True, 'font_size': '20px'})
        cell_head_format = workbook.add_format({'font_size': '12px'})
        cell_data_format = workbook.add_format({'font_size': '10px'})
        txt_head = workbook.add_format({'font_size': '10px', 'border': 2})
        txt = workbook.add_format({'font_size': '10px', 'border': 2})
        sheet.merge_range('F2:M3', 'EVENT MANAGEMENT REPORT', head)
        sheet.merge_range('B4:E4', data['company'][0], cell_head_format)
        sheet.merge_range('B5:E5', data['company'][1], cell_head_format)
        sheet.write('B6', 'Date:', cell_head_format)
        sheet.merge_range('C6:E6', data['today_date'], cell_data_format)
        if data['date_from'] and data['date_to'] and data['customer']:
            customer_name = self.env['res.partner'].browse(int(
                data['customer'])).name
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', data['date_from'], cell_data_format)
            sheet.write('F8', 'To:', cell_head_format)
            sheet.merge_range('G8:H8', data['date_to'], cell_data_format)
            sheet.merge_range('J8:K8', 'Customer:', cell_head_format)
            sheet.merge_range('L8:N8', customer_name, cell_data_format)
        elif data['date_from'] and data['date_to']:
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', data['date_from'],
                              cell_data_format)
            sheet.write('F8', 'To:', cell_head_format)
            sheet.merge_range('G8:H8', data['date_to'], cell_data_format)
        elif data['date_from'] and data['customer']:
            customer_name = self.env['res.partner'].browse(int(
                data['customer'])).name
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', data['date_from'], cell_data_format)
            sheet.merge_range('F8:G8', 'Customer:', cell_head_format)
            sheet.merge_range('H8:J8', customer_name, cell_data_format)
        elif data['customer'] and data['date_to']:
            customer_name = self.env['res.partner'].browse(int(
                data['customer'])).name
            sheet.write('B8', 'To:', cell_head_format)
            sheet.merge_range('C8:D8', data['date_to'], cell_data_format)
            sheet.merge_range('F8:G8', 'Customer:', cell_head_format)
            sheet.merge_range('H8:J8', customer_name, cell_data_format)
        elif data['date_from']:
            sheet.write('B8', 'From:', cell_head_format)
            sheet.merge_range('C8:D8', data['date_from'], cell_data_format)
        elif data['date_to']:
            sheet.write('B8', 'To:', cell_head_format)
            sheet.merge_range('C8:D8', data['date_to'], cell_data_format)
        elif data['customer']:
            customer_name = self.env['res.partner'].browse(int(
                data['customer'])).name
            sheet.merge_range('B8:C8', 'Customer:', cell_head_format)
            sheet.merge_range('D8:E8', customer_name, cell_data_format)
        sheet.write(10, 0, 'Sl.no', txt_head)
        sheet.merge_range('B11:E11', 'Name', txt_head)
        sheet.merge_range('F11:H11', 'Type', txt_head)
        sheet.merge_range('I11:K11', 'Customer', txt_head)
        sheet.merge_range('L11:M11', 'Date', txt_head)
        sheet.merge_range('N11:O11', 'Start Date', txt_head)
        sheet.merge_range('P11:Q11', 'End Date', txt_head)
        sheet.write(10, 17, 'State', txt_head)
        where = '1=1'
        if data["customer"]:
            where += """AND e.partner_id = %s""" % int(data['customer'])
        if data['date_from']:
            where += """AND e.date>='%s'""" % (data['date_from'])
        if data['date_to']:
            where += """AND e.date <= '%s'""" % (data['date_to'])
        if data['event_type']:
            event_list = data['event_type']
            event_ids = f"({event_list[0]})" if len(
                event_list) == 1 else tuple(event_list)
            where += """AND e.type_of_event_id IN {}""".format(event_ids)
        if data['state']:
            where += """AND e.state = '%s'""" % (data['state'])
        self.env.cr.execute("""
                SELECT e.name as event, t.name as type, r.name as partner, 
                e.state, e.date,
                e.start_date, e.end_date
                from event_management e inner join 
                res_partner r on e.partner_id = r.id
                inner join event_management_type t on 
                e.type_of_event_id = t.id
                where %s order by e.date""" % where)
        rec = self.env.cr.fetchall()
        col = 11
        row = 1
        for i in range(0, len(rec)):
            sheet.write(col, 0, row, txt)
            sheet.merge_range('B%d:E%d' % (col + 1, col + 1), rec[i][0], txt)
            sheet.merge_range('F%d:H%d' % (col + 1, col + 1), rec[i][1], txt)
            sheet.merge_range('I%d:K%d' % (col + 1, col + 1), rec[i][2], txt)
            sheet.merge_range('L%d:M%d' % (col + 1, col + 1),
                              fields.Date.to_string(rec[i][4]), txt)
            sheet.merge_range('N%d:O%d' % (col + 1, col + 1),
                              fields.Datetime.to_string(rec[i][5]), txt)
            sheet.merge_range('P%d:Q%d' % (col + 1, col + 1),
                              fields.Datetime.to_string(rec[i][6]), txt)
            sheet.write(col, 17,
                        dict(self.env['event.management']._fields[
                                 'state'].selection).get(rec[i][3]), txt)
            col += 1
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
