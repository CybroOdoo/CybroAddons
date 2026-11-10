# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.info)
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
import re
from collections import OrderedDict
from odoo import api, exceptions, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class ReportPDF(models.Model):
    """Class to handle PDF Report model"""
    _name = 'report.pdf'
    _description = 'PDF Reports'
    _order = 'id DESC'

    name = fields.Char(help="Name of the report")
    model_id = fields.Many2one(
        'ir.model', required=True,
        ondelete="cascade", help="Name of the model")
    fields_ids = fields.One2many(
        'report.pdf.field',
        'report_id',
        required=True,
        help="Name of the fields")
    date_field_id = fields.Many2one(
        'ir.model.fields',
        string='Date Filter',
        ondelete="cascade",
        help="Name of the fields",
    )
    start_date = fields.Date(help="Set the start date")
    end_date = fields.Date(help="Set the end date")
    field_order = fields.Char(default='[]',
                              help="First order")
    is_action_button = fields.Boolean(default=False, string="Action button",
                                   help="Action button")
    binding_model_id = fields.Many2one('ir.model',
                                       ondelete="cascade",
                                       string="Binding model",
                                       help="Choose binding model")
    binding_type = fields.Selection([
        ('action', 'Action'), ('report', 'Report')],
        required=True, default='action',
        help="Choose binding type")
    action_id = fields.Many2one(
        'ir.actions.act_window',
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
                raise ValidationError(_(
                    'The Start Date And End Date Is Misplaced'))

    @api.constrains('fields_ids')
    def _check_fields_ids(self):
        """Checks whether the user has entered least one fields for the report"""
        if not self.fields_ids:
            raise exceptions.ValidationError(_('Please select a field.'))

    @api.model
    def _format_value(self, field_obj, record, field_name):
        """Return a printable value for one field of one record."""
        value = record[field_name]
        ttype = field_obj.ttype
        if ttype == 'datetime':
            return value.strftime("%d/%m/%Y") if value else ""
        if ttype == 'boolean':
            return "Yes" if value else "No"
        if ttype == 'monetary':
            currency = record.currency_id if 'currency_id' in record else False
            if not currency:
                return str(value)
            if currency.position == 'before':
                return "%s%s" % (currency.symbol, value)
            return "%s%s" % (value, currency.symbol)
        if ttype in ('many2one', 'many2one_reference'):
            return value.display_name if value else "Null"
        if ttype in ('many2many', 'one2many'):
            return ", ".join(value.mapped('display_name')) if value else "Null"
        return value

    def _get_report_data(self, records=None):
        """Build the data dict rendered by the QWeb template.

        :param records: optional recordset of the report model to print.
            When omitted every record matching the date filter is used.
        """
        self.ensure_one()
        rec = self
        domain = []
        if rec.date_field_id and rec.start_date:
            domain.append((rec.date_field_id.name, '>=', rec.start_date))
        if rec.date_field_id and rec.end_date:
            domain.append((rec.date_field_id.name, '<=', rec.end_date))
        Model = self.env[rec.model_id.model]
        if records is None:
            model_data = Model.search(domain)
        else:
            model_data = records.filtered_domain(domain)
        order = [int(i) for i in re.findall(r'\d+', rec.field_order or '')]
        child_fields = rec.fields_ids.one2many_model_field_ids
        table_data = []
        child_table_data = []
        rec_currency_symbol = ''
        for record in model_data:
            if 'currency_id' in record:
                rec_currency_symbol = record.currency_id.symbol or ''
            data_list = []
            list_b = []
            for field_id in order:
                field_obj = self.env['ir.model.fields'].browse(field_id)
                field_name = field_obj.name
                if field_obj.ttype == 'one2many' and record[field_name] \
                        and child_fields:
                    list_b = []
                    for o2m_rec in record[field_name]:
                        list_b.append([
                            self._format_value(c_field, o2m_rec, c_field.name)
                            for c_field in child_fields])
                    field_data = list_b[-1]
                else:
                    field_data = self._format_value(
                        field_obj, record, field_name)
                data_list.append(field_data)
            table_data.append(data_list)
            child_table_data.append(list_b)
        child_field_label = ""
        if child_fields:
            child_field_label = child_fields.mapped('field_description')
        field_heading = {}
        for field in rec.fields_ids.report_field_id:
            field_heading[field.field_description] = (
                field.ttype, field.field_description, rec_currency_symbol)
        return {
            'report_name': rec.name,
            'model_name': rec.model_id.model,
            'fields_name': rec.fields_ids.report_field_id.mapped('name'),
            'field_label': OrderedDict(field_heading),
            'date_field_id': rec.date_field_id.name,
            'date_name': rec.date_field_id.field_description,
            'start_date': rec.start_date,
            'end_date': rec.end_date,
            'field_order': rec.field_order,
            'table_data': table_data,
            'child_field_data': child_table_data,
            'child_field_label': child_field_label,
            'today_date': fields.Datetime.now(),
        }

    def action_print_report(self, records=None):
        """Print the report. Used by the form button (all matching records)
        and by the wizard (only the selected records)."""
        self.ensure_one()
        return self.env.ref(
            'pdf_report_designer.action_report_print_pdf_designer'
        ).report_action(self, data=self._get_report_data(records))

    def action_unlink_action(self):
        """Unlink an action button and reload the view."""
        self.ensure_one()
        if self.action_id:
            # Remove the action window
            self.action_id.unlink()
            self.write({
                'action_id': False,
                'is_action_button': False
            })
        else:
            self.is_action_button = False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_create_model(self):
        """Create a contextual action for each server action."""
        self.is_action_button = True
        windowaction = self.env['ir.actions.act_window']
        for rec in self.browse(self._ids):
            binding_model_id = rec.model_id.id
            view_id = self.env.ref(
                'pdf_report_designer.pdf_report_view_form').id
            button_name = _('Print Report (%s)') % rec.name
            act_id = windowaction.create({
                'name': button_name,
                'is_action_created_from_pdf_report':True,
                'type': 'ir.actions.act_window',
                'res_model': 'pdf.report',
                'binding_model_id': binding_model_id,
                'context': "{'pdf' : %d}" % rec.id,
                'view_mode': 'form,list',
                'view_id': view_id,
                'target': 'new',
            })
            rec.write({
                'action_id': act_id.id,
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
        self.field_order = str(
            self.fields_ids.report_field_id._origin.ids)

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
