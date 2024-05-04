# -*- coding: utf-8 -*-
################################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#   This program is free software: you can modify
#   it under the terms of the GNU Affero General Public License (AGPL) as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models, _

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
import io
import json
import datetime
from odoo.tools import date_utils


class ReportExcel(models.Model):
    """this is used to create the a binding action"""
    _name = 'report.excel'
    _description = "report excel"
    _rec_name = 'name'

    name = fields.Char(string='Name', help='Name')
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               ondelete="cascade", help="The binding model")
    fields_ids = fields.Many2many('ir.model.fields',
                                  string='Fields',
                                  required=True, ondelete="cascade",
                                  help="the fields to be printed in the report")
    date_field = fields.Many2one('ir.model.fields',
                                 string='Date Filter',
                                 ondelete="cascade",
                                 help="filter on the basis of date")
    start_date = fields.Date(string='Start Date', help="start date")
    end_date = fields.Date(string='End Date', help="end date")
    field_order = fields.Char(string="Field Order", default='[]',
                              help="the field order")
    action_button = fields.Boolean(default=False, string="Action",
                                   help="visibility of action")
    state = fields.Selection([
        ('code', 'Execute Python Code'),
        ('object_create', 'Create a new Record'),
        ('object_write', 'Update the Record'),
        ('multi', 'Execute several actions')], string='Action To Do',
        default='code', required=True, copy=True,
        help="to execute the code on the basis")
    binding_model_id = fields.Many2one('ir.model',
                                       ondelete="cascade",
                                       string="Binding Model Id",
                                       help="binding model id")
    binding_type = fields.Selection([('action', 'Action'),
                                     ('report', 'Report')],
                                    required=True, default='action',
                                    string="Binding Type",
                                    help="binding type")
    ir_act_server_ref = fields.Many2one('ir.actions.act_window',
                                        readonly=True,
                                        copy=False, string="Action Reference",
                                        help="action reference")
    fields_ids_domain = fields.Char(compute="_compute_fields_ids_domain",
                                    readonly=True, store=False)
    date_field_domain = fields.Char(compute="_compute_date_field_domain",
                                    readonly=True, store=False)

    @api.depends('model_id')
    def _compute_fields_ids_domain(self):
        """Domain for fields_ids"""
        for rec in self:
            rec.fields_ids_domain = json.dumps(
                [('model_id', '=', rec.model_id.id)]
            )

    @api.depends('model_id')
    def _compute_date_field_domain(self):
        """Domain for date_field"""
        for rec in self:
            rec.date_field_domain = json.dumps(
                [('model_id', '=', rec.model_id.id),
                 ('ttype', 'in', ['date', 'datetime'])]
            )

    @api.onchange('model_id')
    def onchange_model_id(self):
        """This is used to return the fields"""
        if self.model_id:
            self.name = self.model_id.name + ' Report'
            self.fields_ids = False
            self.date_field = False

    def print_report(self):
        """Create a function for printing reports"""
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
                'report_type': 'xlsx',
            }

    def get_xlsx_report(self, data, response):
        """this is used to print the report of all records"""
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
            {'font_size': 10, 'num_format': 'yyyy-m-d', 'align': 'center',
             'bold': True})
        format5 = workbook.add_format(
            {'font_size': 10, 'border': 1, 'text_wrap': True})
        format6 = workbook.add_format({'font_size': 10, 'bold': True})
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
        records = []
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
        new_table = []
        for record in records:
            order = data['field_order'].strip('][').split(', ')
            record_dict = {}
            for field_id in order:
                field = self.env['ir.model.fields'].browse(int(field_id))
                field_name = field.name
                field_type = self.env['ir.model.fields'].browse(
                    int(field_id)).ttype
                if field_type in ['many2many']:
                    one2many_values = ', '.join(
                        record[field_name].mapped('name'))
                    record_dict[field] = [one2many_values]
                elif field_type in ['one2many']:
                    o2m_list = []
                    for rec in record[field_name]:
                        if rec:
                            o2m_list.append(rec)
                        else:
                            o2m_list.append('')
                    record_dict[field] = o2m_list
                else:
                    record_dict[field] = [record[field_name]]
            new_table.append(record_dict)
        for record in new_table:
            col_num = 1
            sheet.write(row_num, col_num, sl_no, format5)
            col_num += 1
            occupied_rows = max(len(value) for value in record.values())
            for field in record:
                field_type = self.env['ir.model.fields'].browse(
                    int(field.id)).ttype
                if not field_type in ['one2many', 'many2many']:
                    try:
                        if isinstance(record[field][0], datetime.date):
                            sheet.write(row_num, col_num, record[field][0],
                                        format10)
                        elif isinstance(record[field][0], bool):
                            if not field:
                                sheet.write(row_num, col_num, " ", format5)
                            else:
                                sheet.write(row_num, col_num, "Yes", format5)
                        else:
                            sheet.write(row_num, col_num, record[field][0],
                                        format5)
                    except Exception as e:
                        if 'display_name' in record[field][0]:
                            sheet.write(row_num, col_num,
                                        record[field][0].display_name, format5)
                        else:
                            sheet.write(row_num, col_num, "", format5)
                elif field_type == 'one2many':
                    for i in range(occupied_rows):
                        if len(record[field]) > i:
                            try:
                                if isinstance(record[field][i], datetime.date):
                                    sheet.write(row_num + i, col_num,
                                                record[field][i], format10)
                                elif isinstance(record[field][i], bool):
                                    if not field:
                                        sheet.write(row_num + i, col_num, "NO",
                                                    format5)
                                    else:
                                        sheet.write(row_num + i, col_num, "Yes",
                                                    format5)
                                else:
                                    sheet.write(row_num + i, col_num,
                                                record[field][i], format5)
                            except Exception as e:
                                if 'display_name' in record[field][i]:
                                    sheet.write(row_num + i, col_num,
                                                record[field][i].display_name, format5)
                                else:
                                    sheet.write(row_num + i, col_num, "",
                                                format5)
                elif field_type == 'many2many':
                    if record[field]:
                        try:
                            if isinstance(record[field], datetime.date):
                                sheet.write(row_num, col_num, record[field][0],
                                            format10)
                            elif isinstance(record[field], bool):
                                if not field:
                                    sheet.write(row_num, col_num, " ", format5)
                                else:
                                    sheet.write(row_num, col_num, "Yes",
                                                format5)
                            else:
                                sheet.write(row_num, col_num, record[field][0],
                                            format5)
                        except Exception as e:
                            if 'display_name' in record[field][0]:
                                sheet.write(row_num, col_num,
                                            record[field].display_name, format5)
                            else:
                                sheet.write(row_num, col_num, "", format5)
                col_num += 1
            row_num += occupied_rows
            sl_no += 1
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
                'res_model': 'excel.report.wizards',
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
        self.ir_act_server_ref.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.onchange('fields_ids')
    def onchange_fields(self):
        """this is used to find the fields of new models"""
        self.fields_ids = []
        if self.fields_ids:
            self.field_order = str(self.fields_ids._origin.ids)
