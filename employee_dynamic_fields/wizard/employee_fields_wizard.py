# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
import xml.etree.ElementTree as xee
from odoo import api, fields, models, _


class EmployeeDynamicFields(models.TransientModel):
    """
       Model for creating dynamic fields and adding necessary fields
    """
    _name = 'employee.dynamic.fields'
    _description = 'Dynamic Fields'
    _inherit = 'ir.model.fields'

    form_view_id = fields.Many2one('ir.ui.view',
                                   string="Form View ID",
                                   help="View ID of the form")

    @api.model
    def get_possible_field_types(self):
        """
           Return all available field types other than 'one2many' and
           'reference' fields.
        """
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    def set_domain(self):
        """Return the fields that currently present in the form"""
        view_id = self.env.ref('hr.view_employee_form')
        view_arch = str(view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'hr.employee')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', field_list)]

    def _set_default(self):
        """
            This method is used to set a default filter in a domain expression
            for the 'hr.employee' model.It retrieves the ID of the
            'hr.employee' model using a search query and sets it as a default
            filter in the domain expression.
        """
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'hr.employee')])
        return [('id', '=', model_id.id)]

    def action_create_fields(self):
        """
           This method is used to create custom fields for the 'hr.employee'
           model and extend the employee form view.It creates a new field in
           the 'ir.model.fields' table, extends the 'hr.view_employee_form'
           view.
        """
        self.env['ir.model.fields'].sudo().create(
            {'name': self.name,
             'field_description': self.field_description,
             'model_id': self.model_id.id,
             'ttype': self.field_type,
             'relation': self.ref_model_id.model,
             'required': self.required,
             'index': self.index,
             'store': self.store,
             'help': self.help,
             'readonly': self.readonly,
             'selection': self.selection_field,
             'copied': self.copied,
             'is_employee_dynamic': True
             })
        inherit_id = self.env.ref('hr.view_employee_form')
        arch_base = _('<?xml version="1.0"?>'
                      '<data>'
                      '<field name="%s" position="%s">'
                      '<field name="%s"/>'
                      '</field>'
                      '</data>') % (
                        self.position_field_id.name, self.position, self.name)
        if self.widget_id:
            arch_base = _('<?xml version="1.0"?>'
                          '<data>'
                          '<field name="%s" position="%s">'
                          '<field name="%s" widget="%s"/>'
                          '</field>'
                          '</data>') % (
                            self.position_field_id.name, self.position,
                            self.name,
                            self.widget.name)

        self.form_view_id = self.env['ir.ui.view'].sudo().create(
            {'name': 'employee.dynamic.fields',
             'type': 'form',
             'model': 'hr.employee',
             'mode': 'extension',
             'inherit_id': inherit_id.id,
             'arch_base': arch_base,
             'active': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    position_field_id = fields.Many2one('ir.model.fields',
                                        string='Field Name',
                                        domain=set_domain, required=True,
                                        ondelete='cascade',
                                        help="Position of the field")
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')], string='Position',
                                required=True)
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               index=True, ondelete='cascade',
                               help="The model this field belongs to",
                               domain=_set_default)
    ref_model_id = fields.Many2one('ir.model', string='Model',
                                   index=True)
    selection_field = fields.Char(string="Selection Options")
    rel_field_id = fields.Many2one('ir.model.fields',
                                string='Related Field')
    field_type = fields.Selection(selection='get_possible_field_types',
                                  string='Field Type', required=True)
    ttype = fields.Selection(string="Field Type", related='field_type',
                             help="Specifies the type of the field")
    widget_id = fields.Many2one('employee.field.widgets',
                             string='Widget', help="Widget of the field")
    groups = fields.Many2many('res.groups',
                              'employee_dynamic_fields_group_rel',
                              'field_id', 'group_id')
    extra_features = fields.Boolean(string="Show Extra Properties",
                                    help="Add extra features for the field")

    @api.depends('field_type')
    @api.onchange('field_type')
    def onchange_field_type(self):
        """
            This method is triggered when the 'field_type' attribute is changed
            in a form. It provides a domain for the 'widget' attribute based on
            the selected field type.
        """
        if self.field_type:
            if self.field_type == 'binary':
                return {'domain': {'widget_id': [('name', '=', 'image')]}}
            elif self.field_type == 'many2many':
                return {'domain': {
                    'widget_id': [('name', 'in', ['many2many_tags', 'binary'])]}}
            elif self.field_type == 'selection':
                return {'domain': {
                    'widget_id': [('name', 'in', ['radio', 'priority'])]}}
            elif self.field_type == 'float':
                return {'domain': {'widget_id': [('name', '=', 'monetary')]}}
            elif self.field_type == 'many2one':
                return {'domain': {'widget_id': [('name', '=', 'selection')]}}
            else:
                return {'domain': {'widget_id': [('id', '=', False)]}}
        return {'domain': {'widget_id': [('id', '=', False)]}}

    def unlink(self):
        """
            This method is used to delete dynamic fields associated with
            an instance of 'EmployeeDynamicFields' and deactivate the related
            form view.
        """
        if self.form_view_id:
            self.form_view_id.active = False
            for field in self:
                query = """delete FROM ir_model_fields WHERE name = %s"""
                self.env.cr.execute(query, [field.name])
        return super(EmployeeDynamicFields, self).unlink()


class HrEmployee(models.Model):
    """
       Inherit the hr.employee model for adding fields
    """
    _description = 'Employee'
    _inherit = 'hr.employee'

    x_currency_id = fields.Many2one('res.currency',
                                    help="Choose currency",
                                    string='Currency')
