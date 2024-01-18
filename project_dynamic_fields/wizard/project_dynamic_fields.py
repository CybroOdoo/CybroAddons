# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
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
#############################################################################
import xml.etree.ElementTree as xee
from odoo import api, fields, models, _


class ProjectDynamicFields(models.TransientModel):
    """Creating new transient model for the wizard from"""
    _name = 'project.dynamic.fields'
    _description = 'Dynamic Fields'
    _inherit = 'ir.model.fields'

    form_view_id = fields.Many2one('ir.ui.view', string="Form View ID",
                                   help="Select the view to be used as"
                                        " the form view for this field.")

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than
         'One2many' and 'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        field_list.remove(('properties', 'properties'))
        field_list.remove(('properties_definition', 'properties_definition'))
        return field_list

    def set_domain(self):
        """Return the fields that currently present in the form"""
        view_id = self.env.ref('project.edit_project')
        view_arch = str(view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'project.project')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', field_list)]

    def _set_default(self):
        """setting the default model"""
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'project.project')])
        return [('id', '=', model_id.id)]

    def action_create_fields(self):
        """ Creates a new custom field for the project.project model and adds
        it to the project form view."""
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
             'is_project_dynamic': True
             })
        inherit_id = self.env.ref('project.edit_project')
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
                            self.widget_id.name)
        self.form_view_id = self.env['ir.ui.view'].sudo().create(
            {'name': 'project.dynamic.fields',
             'type': 'form',
             'model': 'project.project',
             'mode': 'extension',
             'inherit_id': inherit_id.id,
             'arch_base': arch_base,
             'active': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    position_field_id = fields.Many2one('ir.model.fields', string='Field Name',
                                        domain=set_domain, required=True,
                                        help="Select the field that will "
                                             "determine the position of"
                                             " the custom field.")
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')], string='Position',
                                required=True, help="Position of field")
    model_id = fields.Many2one('ir.model', string='Model', required=True,
                               index=True, ondelete='cascade',
                               help="The model this field belongs to",
                               domain=_set_default)
    ref_model_id = fields.Many2one('ir.model', string='Model', index=True,
                                   help="This field is used to specify the "
                                        "model that the dynamic field will be "
                                        "associated with.")
    selection_field = fields.Char(string="Selection Options",
                                  help='Enter selection value')
    rel_field_id = fields.Many2one('ir.model.fields', string='Related Field',
                                   help='Related field')
    field_type = fields.Selection(selection='get_possible_field_types',
                                  string='Field Type', required=True,
                                  help='The type of field that will be '
                                       'created for this dynamic field.'
                                       'This field is required and must be '
                                       'set to one of the possible'
                                       'field types returned by the '
                                       '"get_possible_field_types" method.')
    ttype = fields.Selection(string="Field Type", related='field_type',
                             help='The type of field that this dynamic field '
                                  'corresponds to.')
    widget_id = fields.Many2one('project.field.widgets', string='Widget',
                                help='Select widget')
    groups = fields.Many2many('res.groups',
                                  'project_dynamic_fields_m2m_group_rel',
                                  'field_ids', 'group_ids',
                                  help='The security groups that have access to '
                                       'this dynamic field.')
    extra_features = fields.Boolean(string="Show Extra Properties",
                                    help="A boolean field that determines "
                                         "whether to display extra properties "
                                         "for this dynamic field in the user "
                                         "interface")

    @api.depends('field_type')
    @api.onchange('field_type')
    def onchange_field_type(self):
        if self.field_type:
            if self.field_type == 'binary':
                return {'domain': {'widget': [('name', '=', 'image')]}}
            elif self.field_type == 'many2many':
                return {'domain': {
                    'widget': [('name', 'in', ['many2many_tags', 'binary'])]}}
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
        """Overrides the default 'unlink' method of the
        'ProjectDynamicFields' model to perform custom deletion logic."""
        if self.form_view_id:
            self.form_view_id.active = False
            for field in self:
                if field.ttype == 'many2many':
                    field: [(5, 0, 0)]
                else:
                    query = """delete FROM ir_model_fields WHERE name = %s"""
                    self.env.cr.execute(query, [field.name])
        return super().unlink()
