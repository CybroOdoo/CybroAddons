# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError


class ReportPDF(models.Model):
    """Class to handle PDF Report model"""
    _name = 'report.pdf'
    _description = 'PDF Reports'
    _order = 'id DESC'

    name = fields.Char(string='Name', help="Name of the report")
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               ondelete="cascade", help="Name of the model")
    fields_ids = fields.One2many('report.pdf.field',
                                 'report_id',
                                 string='Fields',
                                 required=True, ondelete="cascade",
                                 help="Name of the fields")
    date_field_id = fields.Many2one('ir.model.fields',
                                    string='Date Filter',
                                    ondelete="cascade",
                                    help="Name of the fields",
                                    )
    start_date = fields.Date(string='Start Date', help="Set the start date")
    end_date = fields.Date(string='End Date', help="Set the end date")
    field_order = fields.Char(default='[]', string="First Order",
                              help="First order")
    action_button = fields.Boolean(default=False, string="Action button",
                                   help="Action button")
    binding_model_id = fields.Many2one('ir.model',
                                       ondelete="cascade",
                                       string="Binding model",
                                       help="Choose binding model")
    binding_type = fields.Selection([('action', 'Action'),
                                     ('report', 'Report')],
                                    required=True, default='action',
                                    string="Binding Type",
                                    help="Choose binding type")
    ir_act_server_ref_id = fields.Many2one('ir.actions.act_window',
                                           readonly=True, copy=False,
                                           string="Server Id",
                                           help="We can get the server id")

    @api.constrains('start_date', 'end_date')
    def _check_start_date_end_date(self):
        """This will give validation at the time of end date and start
        date have any problem or mismatch"""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date or fields.Date.today() > \
                    self.end_date:
                raise ValidationError(
                    'The Start Date And End Date Is Misplaced')

    @api.constrains('fields_ids')
    def _check_fields_ids(self):
        """ Checks whether the user has entered least one fields for the
        report"""
        if not self.fields_ids:
            raise exceptions.ValidationError('Please select a field.')

    def action_print_report(self):
        """ When the user requests to print the report, this function will be
        called. Parameters and return values of the function is noted below.
        @param self: The current report.pdf record. @return: A dictionary
        with report data like field headers and field datas.
        """
        for rec in self:
            domain = []
            if rec.date_field_id and rec.start_date:
                domain.append((rec.date_field_id.name, '>=', rec.start_date))
            if rec.date_field_id and rec.end_date:
                domain.append((rec.date_field_id.name, '<=', rec.end_date))
            if rec.date_field_id and(rec.start_date and rec.end_date):
                domain = [(rec.date_field_id.name, '>=', rec.start_date),
                          (rec.date_field_id.name, '<=', rec.end_date)]
            model_data = self.env[rec.model_id.model].search(domain)
            table_data = []
            child_table_data = []
            rec_currency_symbol = ''
            for record in model_data:
                rec_currency_symbol = record.currency_id.symbol
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
                    elif field_obj.ttype == 'monetary':
                        if record.currency_id.position == 'before':
                            field_data = record.currency_id.symbol+str(record[field_name])
                        else:
                            field_data = str(record[field_name])+record.currency_id.symbol
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
                    field.ttype, field.field_description,rec_currency_symbol)})
            ordered_field_heading = OrderedDict(
               list(field_heading.items()))
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
                'pdf_report_designer.action_report_print_pdf_designer').report_action(
                self, data=data)

    def action_unlink_action(self):
        """
        Unlink an action button and reload the view.
        """
        self.ensure_one()
        if self.ir_act_server_ref_id:
            # Remove the action window
            self.ir_act_server_ref_id.unlink()
            self.write({
                'ir_act_server_ref_id': False,
                'action_button': False
            })
        else:
            self.action_button = False

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_create_model(self):
        """ Create a contextual action for each server action."""
        self.action_button = True
        windowaction = self.env['ir.actions.act_window']
        data = self.env['ir.model.data']
        for rec in self.browse(self._ids):
            binding_model_id = rec.model_id.id
            model_data_id = data._load_xmlid('pdf_report_designer')
            res_id = data.browse(model_data_id).res_id
            button_name = _('Print Report (%s)') % rec.name
            act_id = windowaction.create({
                'name': button_name,
                'is_action_created_from_pdf_report':True,
                'type': 'ir.actions.act_window',
                'res_model': 'pdf.report',
                'binding_model_id': binding_model_id,
                'context': "{'pdf' : %d}" % rec.id,
                'view_mode': 'form,tree',
                'view_id': res_id,
                'target': 'new',
            })
            rec.write({
                'ir_act_server_ref_id': act_id.id,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.onchange('fields_ids')
    def _onchange_fields_ids(self):
        """
        This method is used to create a list of selected fields ids
        @param self: object pointer
        """
        self.fields_ids = []
        if self.fields_ids:
            self.field_order = str(self.fields_ids.report_field_id._origin.ids)

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """
        This method is used to return domain on date_field_id on change of
        model_id @param self: object pointer @return: returns a domain on
        date_field_id field based on selected model id."""
        if self.model_id:
            self.fields_ids = False
            self.date_field_id = False
        return {
            'domain': {
                'date_field_id': [('model_id', '=', self.model_id),
                                  ('ttype', 'in', ('date', 'datetime'))],
            }
        }

    def unlink(self):
        """ Regular unlink method, but make sure to clear the caches. """
        for attachment in self:
            action_rec = _('Print Report (%s)') % attachment.name
            actions = self.env['ir.actions.act_window'].search(
                [('name', '=', action_rec)])
            actions.unlink()
        super(ReportPDF, self).unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
