# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Ruksana P (<https://www.cybrosys.com>)
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
################################################################################
from xlrd.xlsx import ET

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DynamicFields(models.Model):
    _name = 'dynamic.fields'
    _rec_name = 'field_description'
    _description = 'Custom Dynamic Fields'
    _inherit = 'ir.model.fields'

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than 'One2many' and
        'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    dynamic_field_id = fields.Many2one('ir.model.fields',
                                       string='Field Name',
                                       required=True, ondelete='cascade',
                                       help='Please Enter the name of field')
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')],
                                string='Position', required=True,
                                help='Select the position of dynamic field '
                                     'relative to reference field')
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               index=True, ondelete='cascade',
                               help="Mention the model name for this field "
                                    "to be added")
    ref_model_id = fields.Many2one('ir.model',
                                   string='Reference Model',
                                   help='Choose the model id for which we want '
                                        'to add field', index=True, )
    selection_field = fields.Char(string="Selection Options",
                                  help='Enter the selection options')
    field_type = fields.Selection(selection='get_possible_field_types',
                                  string='Field Type', required=True,
                                  help='Select the field type here')
    ttype = fields.Selection(string="Field Type", related='field_type',
                             help='Select the field type here')
    widget_id = fields.Many2one('dynamic.field.widgets',
                                string='Widget',
                                help='Choose the field widget')
    groups = fields.Many2many('res.groups',
                              'employee_dynamic_fields_group_rel',
                              'field_id', 'group_id',
                              string='Group',
                              help='Enter the group for which this field is'
                                   ' visible')
    is_extra_features = fields.Boolean(string="Show Extra Properties",
                                       help='Please enable this field for extra'
                                            ' attributes')
    status = fields.Selection([('draft', 'Draft'),
                               ('form', 'Field Created'),
                               ('tree', 'Added in Tree View')],
                              string='Status',
                              index=True, readonly=True, tracking=True,
                              copy=False, default='draft',
                              help='The status of dynamic field creation')
    form_view_id = fields.Many2one('ir.ui.view',
                                   string="Form View ID",
                                   required=True,
                                   help='Enter the form view id')
    form_view_inherit = fields.Char(string="Form View Inherit Id",
                                    related='form_view_id.xml_id',
                                    help='Enter the inherited form view id')
    custom_form_view_id = fields.Many2one('ir.ui.view',
                                          string="Form View ID",
                                          help='Enter the custom form view id')
    is_field_in_tree = fields.Boolean(string="Add Field to the Tree View",
                                      help='Enable for tree view')
    tree_view_id = fields.Many2one('ir.ui.view',
                                   string="Tree View ID",
                                   help='Enter the tree view id', )
    tree_view_inherit = fields.Char(string="Tree View Inherit Id",
                                    related='tree_view_id.xml_id',
                                    help='Enter the inherited tree view id')
    custom_tree_view_id = fields.Many2one('ir.ui.view',
                                          string="Tree View ID",
                                          help='Enter the custom tree view id')
    tree_field_ids = fields.Many2many('ir.model.fields',
                                      string='Tree field domain field',
                                      compute='_compute_tree_field_ids',
                                      help='Tree fields domain')
    tree_field_id = fields.Many2one('ir.model.fields',
                                    string='Tree Field',
                                    domain="[('id', 'in', "
                                           "tree_field_ids)]",
                                    help='Tree field')
    tree_field_position = fields.Selection([('before', 'Before'),
                                            ('after', 'After')],
                                           string='Position',
                                           help='Select the position of '
                                                'dynamic field relative to '
                                                'reference field in tree view')
    is_visible_in_tree_view = fields.Boolean(string='Visible in tree view',
                                             help='Weather toggle visible the '
                                                  'newly created field in '
                                                  'tree view')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Return the corresponding form, tree view id and field records"""
        form_view_ids = self.model_id.view_ids.filtered(
            lambda l: l.type == 'form' and l.mode == 'primary')
        tree_view_ids = self.model_id.view_ids.filtered(
            lambda l: l.type == 'tree' and l.mode == 'primary')
        field_records = self.env['ir.model.fields'].sudo().search([
            ('model', '=', self.model_id.model)])
        field_list = [field.id for rec in field_records for field in rec]
        return {'domain': {
            'form_view_id': [('id', 'in', form_view_ids.ids)],
            'tree_view_id': [('id', 'in', tree_view_ids.ids)],
            'dynamic_field_id': [('id', 'in', field_list)]
        }}

    @api.depends('tree_view_id')
    def _compute_tree_field_ids(self):
        """Compute function to find the tree view fields of selected tree view
               in field tree_view_id"""
        for rec in self:
            if rec.tree_view_id:
                field_list = []
                if rec.tree_view_id.xml_id:
                    tree_fields = ET.fromstring(self.env.ref(
                        rec.tree_view_id.xml_id).arch).findall(".//field")
                    for field in tree_fields:
                        field_list.append(field.get('name'))
                inherit_id = rec.tree_view_id.inherit_id \
                    if rec.tree_view_id.inherit_id else False
                while inherit_id:
                    if inherit_id.xml_id:
                        tree_fields = ET.fromstring(self.env.ref(
                            inherit_id.xml_id).arch).findall(".//field")
                        for field in tree_fields:
                            field_list.append(field.get('name'))
                    inherit_id = inherit_id.inherit_id \
                        if inherit_id.inherit_id else False
                self.tree_field_ids = self.env['ir.model.fields'].search(
                    [('model_id', '=', self.model_id.id),
                     ('name', 'in', field_list)])
            else:
                rec.tree_field_ids = False

    @api.onchange('field_type')
    def _onchange_field_type(self):
        """When changing field type, this method returns widget of
        corresponding field type"""
        widget_mapping = {
            'binary': [('name', '=', 'image')],
            'many2many': [('name', 'in', ['many2many_tags', 'binary'])],
            'selection': [('name', 'in', ['radio', 'priority'])],
            'float': [('name', '=', 'monetary')],
            'many2one': [('name', '=', 'selection')],
        }
        return {'domain': {'widget_id': widget_mapping.get(self.field_type,
                                                        [('id', '=', False)])}}

    def action_create_dynamic_fields(self):
        """ The 'CREATE FIELD' button method is used to add new field to form
         view of required model"""
        self.write({'status': 'form'})
        if self.field_type == 'monetary' and not self.env[
            'ir.model.fields'].sudo().search([('model', '=', self.model_id.id),
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
            self.form_view_id.name) + ".inherit.dynamic.custom." + str(
            self.field_description) + ".field"
        xml_id = self.form_view_id.xml_id
        inherit_id = self.env.ref(xml_id)
        arch_base = _('<?xml version="1.0"?>'
                      '<data>'
                      '<field name="%s" position="%s">'
                      '<field name="%s"/>'
                      '</field>'
                      '</data>') % (self.dynamic_field_id.name,
                                    self.position, self.name)
        if self.widget_id:
            arch_base = _('<?xml version="1.0"?>'
                          '<data>'
                          '<field name="%s" position="%s">'
                          '<field name="%s" widget="%s"/>'
                          '</field>'
                          '</data>') % (self.dynamic_field_id.name,
                                        self.position, self.name,
                                        self.widget_id.name)
        self.custom_form_view_id = self.env['ir.ui.view'].sudo().create({
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

    def action_add_field_to_tree_view(self):
        """ Button 'Add to Tree View' is used add the created dynamic field to
        tree view of corresponding model"""
        tree_view = self.env['ir.ui.view'].search(
            [('model', '=', self.model_id.model), ('type', '=', 'tree')])
        view_id_tree = self.env.ref(self.tree_view_inherit)
        if tree_view and view_id_tree.arch:
            if self.is_field_in_tree:
                inherit_tree_view_name = str(
                    self.tree_view_id.name) + ".inherit.dynamic.custom" + \
                                         str(self.field_description) + ".field"
                optional = "show" if self.is_visible_in_tree_view else "hide"
                tree_view_arch_base = (_(f'''
                                    <data>
                                        <xpath expr="//field[@name='{self.tree_field_id.name}']" position="{self.tree_field_position}">
                                            <field name="{self.name}" optional="{optional}"/>
                                        </xpath>
                                    </data>'''))
                self.custom_tree_view_id = self.env['ir.ui.view'].sudo().create(
                    {'name': inherit_tree_view_name,
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
                _('Error! Selected Model You cannot add a custom field to the '
                  'tree view.'))

    @api.onchange('model_id', 'is_field_in_tree')
    def onchange_domain(self):
        """Return the fields that currently present in the form"""
        form_view_ids = self.model_id.view_ids.filtered(
            lambda x: x.type == 'form' and x.mode == 'primary')
        tree_view_ids = self.model_id.view_ids.filtered(
            lambda x: x.type == 'tree' and x.mode == 'primary')
        field_records = self.env['ir.model.fields'].sudo().search([
            ('model', '=', self.model_id.model)])
        field_list = [field.id for record in field_records for field in record]
        return {'domain': {
            'form_view_id': [('id', 'in', form_view_ids.ids)],
            'tree_view_id': [('id', 'in', tree_view_ids.ids)],
            'position_field': [('id', 'in', field_list)]
        }}

    @api.onchange('field_type')
    def onchange_field_type(self):
        """"Onchange method of field_type, when changing field type it will
        return domain for widget """
        widget_mappings = {
            'binary': [('name', '=', 'image')],
            'many2many': [('name', 'in', ['many2many_tags', 'binary'])],
            'selection': [('name', 'in', ['radio', 'priority'])],
            'float': [('name', '=', 'monetary')],
            'many2one': [('name', '=', 'selection')],
        }
        return {'domain': {'widget': widget_mappings.get(self.field_type,
                                                         [('id', '=', False)])}}

    def unlink(self):
        """ Unlinking method of dynamic field"""
        if self.form_view_id:
            self.custom_form_view_id.active = False
        if self.tree_view_id:
            self.custom_tree_view_id.active = False
        result = super().unlink()
        return result
