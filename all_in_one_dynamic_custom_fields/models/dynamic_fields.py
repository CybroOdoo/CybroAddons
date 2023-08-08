# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DynamicFields(models.Model):
    _name = 'dynamic.fields'
    _rec_name = 'field_description'
    _description = 'Custom Dynamic Fields'
    _inherit = 'ir.model.fields'

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than 'one2many' and
        'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    position_field = fields.Many2one('ir.model.fields', string='Field Name',
                                     required=True,
                                     ondelete='cascade')
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')], string='Position',
                                required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True,
                               index=True, ondelete='cascade',
                               help="The model this field belongs to")
    ref_model_id = fields.Many2one('ir.model', string='Model', index=True)
    selection_field = fields.Char(string="Selection Options")
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')
    field_type = fields.Selection(selection='get_possible_field_types',
                                  string='Field Type', required=True)
    ttype = fields.Selection(string="Field Type", related='field_type')
    widget = fields.Many2one('dynamic.field.widgets', string='Widget')
    groups = fields.Many2many('res.groups', 'employee_dynamic_fields_group_rel',
                              'field_id', 'group_id')
    extra_features = fields.Boolean(string="Show Extra Properties")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('form', 'Field Created'),
        ('tree', 'Added in Tree View'),
    ], string='Status', index=True, readonly=True, tracking=True,
        copy=False, default='draft',
        required=True, help='Record Status')

    form_view_id = fields.Many2one('ir.ui.view', string="Form View ID",
                                   required=True)
    form_view_inherit_id = fields.Char(string="Form View Inherit Id",
                                       related='form_view_id.xml_id')
    add_field_in_tree = fields.Boolean(string="Add Field to the Tree View",
                                       default=False)
    tree_view_id = fields.Many2one('ir.ui.view', string="Tree View ID")
    tree_view_inherit_id = fields.Char(string="Tree View Inherit Id",
                                       related='tree_view_id.xml_id')

    def create_dynamic_fields(self):
        self.write({'status': 'form'})
        if self.field_type == 'monetary' and not self.env[
            'ir.model.fields'].sudo().search([
            ('model', '=', self.model_id.id),
            ('name', '=', 'currency_id')]):
            self.env['ir.model.fields'].sudo().create({
                'name': 'x_currency_id',
                'field_description': 'Currency',
                'model_id': self.model_id.id,
                'ttype': 'many2one',
                'relation': 'res.currency',
                'is_dynamic_field': True
            })
        self.env['ir.model.fields'].sudo().create({
            'name': self.name,
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
            'is_dynamic_field': True
        })
        inherit_form_view_name = str(
            self.form_view_id.name) + ".inherit.dynamic.custom." + \
                                 str(self.field_description) + ".field"
        xml_id = self.form_view_id.xml_id
        inherit_id = self.env.ref(xml_id)
        arch_base = _('<?xml version="1.0"?>'
                      '<data>'
                      '<field name="%s" position="%s">'
                      '<field name="%s"/>'
                      '</field>'
                      '</data>') % (self.position_field.name,
                                    self.position, self.name)
        if self.widget:
            arch_base = _('<?xml version="1.0"?>'
                          '<data>'
                          '<field name="%s" position="%s">'
                          '<field name="%s" widget="%s"/>'
                          '</field>'
                          '</data>') % (self.position_field.name,
                                        self.position, self.name,
                                        self.widget.name)
        self.form_view_id = self.env['ir.ui.view'].sudo().create({
            'name': inherit_form_view_name,
            'type': 'form',
            'model': self.model_id.model,
            'mode': 'extension',
            'inherit_id': inherit_id.id,
            'arch_base': arch_base,
            'active': True
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def add_field_to_tree_view(self):
        if self.add_field_in_tree:
            if self.add_field_in_tree:
                inherit_tree_view_name = str(
                    self.tree_view_id.name) + ".inherit.dynamic.custom" + \
                                         str(self.field_description) + ".field"
                tree_view_arch_base = _(
                    '<?xml version="1.0"?>'
                    '<data>'
                    '''<xpath expr="//tree" position="inside">'''
                    '''<field name="%s" optional="show"/>'''
                    '''</xpath>'''
                    '''</data>''') % self.name
                self.tree_view_id = self.env['ir.ui.view'].sudo().create({
                    'name': inherit_tree_view_name,
                    'type': 'tree',
                    'model': self.model_id.model,
                    'mode': 'extension',
                    'inherit_id': self.tree_view_id.id,
                    'arch_base': tree_view_arch_base,
                    'active': True})
                self.write({'status': 'tree'})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
        else:
            raise ValidationError(
                _('Error! Please select the boolean field Add Field to the Tree View.'))

    @api.depends('model_id','add_field_in_tree')
    @api.onchange('model_id','add_field_in_tree')
    def set_domain(self):
        """Return the fields that currently present in the form"""
        form_view_ids = self.model_id.view_ids.filtered(
            lambda l: l.type == 'form' and l.mode == 'primary')
        tree_view_ids = self.model_id.view_ids.filtered(
            lambda l: l.type == 'tree' and l.mode == 'primary')
        fields = self.env['ir.model.fields'].sudo().search([
            ('model', '=', self.model_id.model)])
        field_list = []
        for rec in fields:
            for field in rec:
                field_list.append(field.id)
        return {'domain': {
            'form_view_id': [('id', 'in', form_view_ids.ids)],
            'tree_view_id': [('id', 'in', tree_view_ids.ids)],
            'position_field': [('id', 'in', field_list)]
        }}

    @api.depends('field_type')
    @api.onchange('field_type')
    def onchange_field_type(self):
        if self.field_type:
            if self.field_type == 'binary':
                return {'domain': {'widget': [('name', '=', 'image')]}}
            elif self.field_type == 'many2many':
                return {'domain': {'widget': [
                    ('name', 'in', ['many2many_tags', 'binary'])]}}
            elif self.field_type == 'selection':
                return {'domain': {
                    'widget': [('name', 'in', ['radio', 'priority'])]}}
            elif self.field_type == 'float':
                return {'domain': {'widget': [('name', '=', 'monetary')]}}
            elif self.field_type == 'many2one':
                return {'domain': {'widget': [('name', '=', 'selection')]}}
            else:
                return {'domain': {'widget': [('id', '=', False)]}}
        return {'domain': {'widget': [('id', '=', False)]}}

    def unlink(self):
        if self.form_view_id:
            self.form_view_id.active = False
        if self.tree_view_id:
            self.tree_view_id.active = False
        res = super(DynamicFields, self).unlink()
        return res
