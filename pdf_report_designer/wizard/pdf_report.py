# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prasanna Kumara B (odoo@cybrosys.com)
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
###############################################################################
from collections import OrderedDict
from odoo import fields, models


class PDFReportWizard(models.TransientModel):
    """Class to manage PDF Report Wizard model"""
    _name = "pdf.report"
    _description = "PDF Report Wizard"
    _order = 'id DESC'

    def action_print_pdf_report(self):
        """
        When the user requests to print the report in the action menu,
        this function will be called. Parameters and return values of the
        function is noted below. :param self: The current report.pdf record.
        :return: A dictionary with report data like field headers and field
        datas.
        """
        record_ids = self.env.context.get('active_ids', [])
        record_model = self.env.context.get('active_model')
        pdf_report_id = self.env['report.pdf'].browse(self._context.get('pdf'))
        for rec in pdf_report_id:
            domain = []
            if rec.date_field_id and rec.start_date:
                domain.append((rec.date_field_id.name, '>=', rec.start_date))
            if rec.date_field_id and rec.end_date:
                domain.append((rec.date_field_id.name, '<=', rec.end_date))
            if rec.date_field_id and (rec.start_date and rec.end_date):
                domain = [(rec.date_field_id.name, '>=', rec.start_date),
                          (rec.date_field_id.name, '<=', rec.end_date)]
            model_records = self.env[record_model].browse(record_ids)
            model_data = model_records.filtered_domain(domain)
            table_data = []
            child_table_data = []
            for record in model_data:
                data_list = []
                list_b = []
                order = rec.field_order.strip('][').split(', ')
                for field_id in order:
                    field_obj = self.env['ir.model.fields'].browse(
                        int(field_id))
                    field_name = field_obj.name
                    if field_obj.ttype == 'datetime':
                        field_data = record[field_name].strftime("%d/%m/%Y")
                    elif field_obj.ttype == 'boolean':
                        if not record[field_name]:
                            field_data = "No"
                        else:
                            field_data = "Yes"
                    elif field_obj.ttype == 'monetary':
                        if record.currency_id.position == 'before':
                            field_data = record.currency_id.symbol+str(record[field_name])
                        else:
                            field_data = str(record[field_name])+record.currency_id.symbol
                    elif field_obj.ttype == 'many2one' or field_obj.ttype == 'many2one_reference':
                        if record[field_name]:
                            field_data = record[field_name].name_get()[0][1]
                        else:
                            field_data = "Null"
                    elif field_obj.ttype == 'many2many':
                        if record[field_name]:
                            field_data = ""
                            for count, value in enumerate(record[field_name]):
                                if not count == len(record[field_name]) - 1:
                                    field_data += value.name_get()[0][1] + ", "
                                else:
                                    field_data += value.name_get()[0][1]
                        else:
                            field_data = "Null"
                    elif field_obj.ttype == 'one2many':
                        if record[field_name]:
                            child_fields = rec.fields_ids.one2many_model_field_ids
                            if child_fields:
                                field_data = "one2many"
                                list_b = []
                                for o2m_c_field in record[field_name]:
                                    list_a = []
                                    for c_field in child_fields:
                                        c_field_name = c_field.name
                                        if c_field.ttype == 'datetime':
                                            child_field_data = o2m_c_field[
                                                c_field_name].strftime(
                                                "%d/%m/%Y")
                                        elif c_field.ttype == 'boolean':
                                            if o2m_c_field[c_field_name]:
                                                child_field_data = "Yes"
                                            else:
                                                child_field_data = "No"
                                        elif c_field.ttype in (
                                                'many2one',
                                                'many2one_reference'):
                                            if o2m_c_field[c_field_name]:
                                                child_field_data = o2m_c_field[
                                                    c_field_name].name_get()[0][
                                                    1]
                                            else:
                                                child_field_data = "Null"
                                        elif c_field.ttype in (
                                                'many2one',
                                                'many2one_reference'):
                                            if o2m_c_field[c_field_name]:
                                                child_field_data = o2m_c_field[
                                                    c_field_name].name_get()[0][
                                                    1]
                                            else:
                                                child_field_data = "Null"
                                        elif c_field.ttype in (
                                                'many2many', 'one2many'):
                                            if o2m_c_field[c_field_name]:
                                                child_field_data = ""
                                                for c_count, c_value in enumerate(
                                                        o2m_c_field[
                                                            c_field_name]):
                                                    if not c_count == len(
                                                            o2m_c_field[
                                                                c_field_name]) - 1:
                                                        child_field_data += \
                                                            c_value.name_get()[
                                                                0][
                                                                1] + ", "
                                                    else:
                                                        child_field_data += \
                                                            c_value.name_get()[
                                                                0][1]
                                            else:
                                                child_field_data = "Null"
                                        else:
                                            child_field_data = o2m_c_field[
                                                c_field_name]
                                        list_a.append(child_field_data)
                                        field_data = list_a
                                    list_b.append(list_a)
                            else:
                                field_data = ""
                                for count, value in enumerate(
                                        record[field_name]):
                                    if not count == len(record[field_name]) - 1:
                                        field_data += value.name_get()[0][
                                                          1] + ", "
                                    else:
                                        field_data += value.name_get()[0][1]
                        else:
                            field_data = "Null"
                    else:
                        field_data = record[field_name]
                    data_list.append(field_data)
                table_data.append(data_list)
                child_table_data.append(list_b)
            child_label = rec.fields_ids.one2many_model_field_ids
            child_field_label = ""
            if child_label:
                child_field_label = child_label.mapped('field_description')
            field_heading = {}
            for field in rec.fields_ids.report_field_id:
                field_heading.update({field.field_description: (
                    field.ttype, field.field_description)})
            ordered_field_heading = OrderedDict(
                reversed(list(field_heading.items())))
            data = {
                'report_name': rec.name,
                'model_name': rec.model_id.model,
                'fields_name': rec.fields_ids.report_field_id.mapped('name'),
                'field_label': ordered_field_heading,
                'date_field_id': rec.date_field_id.name,
                'date_name': rec.date_field_id.field_description,
                'start_date': rec.start_date,
                'end_date': rec.end_date,
                'field_order': rec.field_order,
                'table_data': table_data,
                'child_field_data': child_table_data,
                'child_field_label': child_field_label,
                'today_date': fields.Datetime.now()
            }
            return self.env.ref(
                'pdf_report_designer.action_wizard_pdf_designer').report_action(
                self, data=data)
