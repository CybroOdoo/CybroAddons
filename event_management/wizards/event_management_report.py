# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Subina P (odoo@cybrosys.com)
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
import pytz
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.tools import date_utils, io, xlsxwriter


class EventManagementReport(models.TransientModel):
    """Creates for event management report"""
    _name = 'event.management.report'
    _description = 'Event Management Report'

    date_from = fields.Date(string="From", help="Start date event")
    date_to = fields.Date(string="To", help="End date of event")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help="Choose a partner whose associated events"
                                      " are to be displayed.")
    type_event_ids = fields.Many2many('event.management.type', 'event_type_rel',
                                      'report_id', 'type_id', string="Type",
                                      help="Type of event management")
    event_state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('invoice', 'Invoiced'),
         ('close', 'Close'), ('cancel', 'Canceled')], string="State",
        help="Choose a state of the event")

    def action_print_pdf_report(self):
        """Method for printing pdf report"""
        type_select = self.type_event_ids.ids
        data = {
            'model': 'event.management.report',
            'form': self.read()[0],
            'event_types': type_select
        }
        return self.env.ref(
            'event_management.report_event_management_action').report_action(
            self, data=data)

    def action_print_xls_report(self):
        """Method of button for printing xlsx report"""
        rec = self.env.user.sudo().company_id
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValidationError('From Date must be less than To Date')
        current = pytz.UTC.localize(fields.datetime.now()).astimezone(pytz.
                                                    timezone(self.env.user.tz))
        data = {
            'event_type': self.type_event_ids.ids,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'customer': self.partner_id.id,
            'state': self.event_state,
            'today_date': current,
            'company': [rec.partner_id.name, rec.street]
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
        sheet.merge_range('L11:M11', 'Register Date', txt_head)
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
        datas = self.env.cr.fetchall()
        row = 11
        col = 1
        for i in range(0, len(datas)):
            sheet.write(row, 0, col, txt)
            sheet.merge_range('B%d:E%d' % (row + 1, row + 1), datas[i][0], txt)
            sheet.merge_range('F%d:H%d' % (row + 1, row + 1), datas[i][1], txt)
            sheet.merge_range('I%d:K%d' % (row + 1, row + 1), datas[i][2], txt)
            sheet.merge_range('L%d:M%d' % (row + 1, row + 1),
                              fields.Date.to_string(datas[i][4]), txt)
            sheet.merge_range('N%d:O%d' % (row + 1, row + 1),
                              fields.Datetime.to_string(datas[i][5]), txt)
            sheet.merge_range('P%d:Q%d' % (row + 1, row + 1),
                              fields.Datetime.to_string(datas[i][6]), txt)
            sheet.write(row, 17,
                        dict(self.env['event.management']._fields[
                                 'state'].selection).get(datas[i][3]), txt)
            row += 1
            col += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
