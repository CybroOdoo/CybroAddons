# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-December Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import models, fields, api, _

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import io
import json
import datetime
from odoo.tools import date_utils


class SelectReportExcel(models.Model):
    _name = 'report.excel'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete="cascade")
    fields_ids = fields.Many2many('ir.model.fields', string='Fields',
                                  required=True, ondelete="cascade")
    date_field = fields.Many2one('ir.model.fields', string='Date Filter', ondelete="cascade")
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    field_order = fields.Char(default='[]')
    action_button = fields.Boolean(default=False)
    state = fields.Selection([
        ('code', 'Execute Python Code'),
        ('object_create', 'Create a new Record'),
        ('object_write', 'Update the Record'),
        ('multi', 'Execute several actions')], string='Action To Do',
        default='code', required=True, copy=True)

    binding_model_id = fields.Many2one('ir.model', ondelete="cascade")
    binding_type = fields.Selection([('action', 'Action'),
                                     ('report', 'Report')],
                                    required=True, default='action')
    ir_act_server_ref = fields.Many2one('ir.actions.act_window', readonly=True, copy=False)

    def print_report(self):

        for rec in self:
            data = {
                'report_name': rec.name,
                'model_name': rec.model_id.model,
                'fields_name': rec.fields_ids.mapped('name'),
                'field_label': rec.fields_ids.mapped('field_description'),
                'date_field': rec.date_field.name,
                'date_name': rec.date_field.field_description,
                'start_date': rec.start_date,
                'end_date': rec.end_date,
                'field_order': rec.field_order
            }
            return {
                'type': 'ir.actions.report',
                'data': {'model': 'report.excel',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': rec.name,
                         },
                'report_type': 'stock_xlsx',
            }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # Formats
        format1 = workbook.add_format(
            {'font_size': 15, 'align': 'center', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format(
            {'font_size': 11, 'bold': True, 'border': 1, 'bg_color': '#928E8E'})
        format4 = workbook.add_format(
            {'font_size': 10, 'num_format': 'yyyy-m-d', 'bold': True})
        format5 = workbook.add_format({'font_size': 10, 'border': 1})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'bold': True})
        format8 = workbook.add_format({'font_size': 10, 'border': 1})
        format9 = workbook.add_format(
            {'font_size': 10, 'num_format': 'yyyy-m-d'})
        format10 = workbook.add_format(
            {'font_size': 10, 'num_format': 'yyyy-m-d', 'border': 1})

        format2.set_align('center')
        format4.set_align('right')
        format6.set_align('right')
        format8.set_align('left')

        sheet.merge_range(1, 1, 1, len(data['field_label']) + 1,
                          data['report_name'], format1)
        sheet.write(2, 0, "Date :", format4)
        sheet.write(2, 1, fields.Datetime.today(), format4)
        if data['date_field']:
            sheet.write(3, 0, data['date_name'], format4)
            if data['start_date']:
                sheet.write(3, 1, "From:", format4)
                sheet.write(3, 2, data['start_date'], format9)
            else:
                sheet.write(3, 2, "", format9)
            if data['end_date']:
                sheet.write(3, 3, "To:", format4)
                sheet.write(3, 4, data['end_date'], format9)
            else:
                sheet.write(3, 4, "", format9)
        sl_no = 1
        sheet.write(5, 1, "SL No", format2)
        row_num = 5
        col_num = 2
        order = data['field_order'].strip('][').split(', ')
        for field_id in order:
            field_name = self.env['ir.model.fields'].browse(
                int(field_id)).field_description
            sheet.write(row_num, col_num, field_name, format2)
            col_num += 1
        row_num += 1
        if data['date_field']:
            if data['start_date'] and data['end_date']:
                records = self.env[data['model_name']].search([
                    (data['date_field'], '>=', data['start_date']),
                    (data['date_field'], '<=', data['end_date'])])
            elif data['start_date'] and not data['end_date']:
                records = self.env[data['model_name']].search([
                    (data['date_field'], '>=', data['start_date'])])
            elif not data['start_date'] and data['end_date']:
                records = self.env[data['model_name']].search([
                    (data['date_field'], '<=', data['end_date'])])
        else:
            records = self.env[data['model_name']].search([])
        table_data = []
        for record in records:
            list = []
            order = data['field_order'].strip('][').split(', ')
            for field_id in order:
                field_name = self.env['ir.model.fields'].browse(
                    int(field_id)).name
                list.append(record[field_name])
            table_data.append(list)
        for record in table_data:
            col_num = 1
            sheet.write(row_num, col_num, sl_no, format5)
            col_num += 1
            for field in record:
                try:
                    if isinstance(field, datetime.date):
                        sheet.write(row_num, col_num, field, format10)
                    elif isinstance(field, bool):
                        if not field:
                            sheet.write(row_num, col_num, " ", format5)
                        else:
                            sheet.write(row_num, col_num, "Yes", format5)
                    else:
                        sheet.write(row_num, col_num, field, format5)
                except Exception as e:
                    if field:
                        sheet.write(row_num, col_num, field.name_get()[0][1],
                                    format5)
                    else:
                        sheet.write(row_num, col_num, "",
                                    format5)
                col_num += 1
            sl_no += 1
            row_num += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def create_model_action(self):
        """ Create a contextual action for each server action."""
        self.action_button = True
        WindowAction = self.env['ir.actions.act_window']
        data = self.env['ir.model.data']
        for rec in self.browse(self._ids):
            binding_model_id = rec.model_id.id
            model_data_id = data._load_xmlid('excel_report_designer')
            res_id = data.browse(model_data_id).res_id
            button_name = _('Print Report (%s)') % rec.name
            act_id = WindowAction.create({
                'name': button_name,
                'type': 'ir.actions.act_window',
                'res_model': 'excel.report.wizard',
                'binding_model_id': binding_model_id,
                'context': "{'excel' : %d}" % (rec.id),
                'view_mode': 'form,tree',
                'view_id': res_id,
                'target': 'new',
            })
            rec.write({
                'ir_act_server_ref': act_id.id,
            })

        return True

    def unlink_model_action(self):
        """ Remove the contextual actions created for the server actions. """
        self.action_button = False
        self.check_access_rights('write', raise_exception=True)
        self.filtered('binding_model_id').write({'binding_model_id': False})
        return True

    @api.onchange('fields_ids')
    def onchange_fields(self):
        self.fields_ids = []
        current_order = self.field_order.strip('][').split(', ')
        if self.fields_ids:
            self.field_order = str(self.fields_ids._origin.ids)

    @api.onchange('model_id')
    def onchange_model_id(self):
        if self.model_id:
            self.name = self.model_id.name + ' Report'
            self.fields_ids = False
            self.date_field = False
            return {
                'domain': {
                    'fields_ids': [('model_id', '=', self.model_id.id)],
                    'date_field': [('model_id', '=', self.model_id.id),
                                   ('ttype', 'in', ['date', 'datetime'])],
                }
            }


class excel_report_wizard(models.TransientModel):
    _name = "excel.report.wizard"

    def print_excel_report(self):
        excel_report_id = self.env['report.excel'].browse(self._context.get('excel'))
        for rec in excel_report_id:
            data = {
                'report_name': rec.name,
                'model_name': rec.model_id.model,
                'fields_name': rec.fields_ids.mapped('name'),
                'field_label': rec.fields_ids.mapped('field_description'),
                'date_field': rec.date_field.name,
                'date_name': rec.date_field.field_description,
                'start_date': rec.start_date,
                'end_date': rec.end_date,
                'field_order': rec.field_order
            }
            return {
                'type': 'ir.actions.report',
                'data': {'model': 'excel.report.wizard',
                         'options': json.dumps(data,
                                               default=date_utils.json_default),
                         'output_format': 'xlsx',
                         'report_name': rec.name,
                         },
                'report_type': 'stock_xlsx',
            }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        # Formats
        format1 = workbook.add_format(
            {'font_size': 15, 'align': 'center', 'bold': True})
        format1.set_font_color('#000080')
        format2 = workbook.add_format(
            {'font_size': 11, 'bold': True, 'border': 1, 'bg_color': '#928E8E'})
        format4 = workbook.add_format(
            {'font_size': 10, 'num_format': 'yyyy-m-d', 'bold': True})
        format5 = workbook.add_format({'font_size': 10, 'border': 1})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
        format7 = workbook.add_format({'font_size': 10, 'bold': True})
        format8 = workbook.add_format({'font_size': 10, 'border': 1})
        format9 = workbook.add_format(
            {'font_size': 10, 'num_format': 'yyyy-m-d'})
        format10 = workbook.add_format(
            {'font_size': 10, 'num_format': 'yyyy-m-d', 'border': 1})

        format2.set_align('center')
        format4.set_align('right')
        format6.set_align('right')
        format8.set_align('left')

        sheet.merge_range(1, 1, 1, len(data['field_label']) + 1,
                          data['report_name'], format1)
        sheet.write(2, 0, "Date :", format4)
        sheet.write(2, 1, fields.Datetime.today(), format4)
        if data['date_field']:
            sheet.write(3, 0, data['date_name'], format4)
            if data['start_date']:
                sheet.write(3, 1, "From:", format4)
                sheet.write(3, 2, data['start_date'], format9)
            else:
                sheet.write(3, 2, "", format9)
            if data['end_date']:
                sheet.write(3, 3, "To:", format4)
                sheet.write(3, 4, data['end_date'], format9)
            else:
                sheet.write(3, 4, "", format9)
        sl_no = 1
        sheet.write(5, 1, "SL No", format2)
        row_num = 5
        col_num = 2
        order = data['field_order'].strip('][').split(', ')
        for field_id in order:
            field_name = self.env['ir.model.fields'].browse(
                int(field_id)).field_description
            sheet.write(row_num, col_num, field_name, format2)
            col_num += 1
        row_num += 1
        if data['date_field']:
            if data['start_date'] and data['end_date']:
                records = self.env[data['model_name']].search([
                    (data['date_field'], '>=', data['start_date']),
                    (data['date_field'], '<=', data['end_date'])])
            elif data['start_date'] and not data['end_date']:
                records = self.env[data['model_name']].search([
                    (data['date_field'], '>=', data['start_date'])])
            elif not data['start_date'] and data['end_date']:
                records = self.env[data['model_name']].search([
                    (data['date_field'], '<=', data['end_date'])])
        else:
            records = self.env[data['model_name']].search([])
        table_data = []
        for record in records:
            list = []
            order = data['field_order'].strip('][').split(', ')
            for field_id in order:
                field_name = self.env['ir.model.fields'].browse(
                    int(field_id)).name
                list.append(record[field_name])
            table_data.append(list)
        for record in table_data:
            col_num = 1
            sheet.write(row_num, col_num, sl_no, format5)
            col_num += 1
            for field in record:
                try:
                    if isinstance(field, datetime.date):
                        sheet.write(row_num, col_num, field, format10)
                    elif isinstance(field, bool):
                        if not field:
                            sheet.write(row_num, col_num, " ", format5)
                        else:
                            sheet.write(row_num, col_num, "Yes", format5)
                    else:
                        sheet.write(row_num, col_num, field, format5)
                except Exception as e:
                    if field:
                        sheet.write(row_num, col_num, field.name_get()[0][1],
                                    format5)
                    else:
                        sheet.write(row_num, col_num, "",
                                    format5)
                col_num += 1
            sl_no += 1
            row_num += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
