# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (<https://www.cybrosys.com>)
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
from bs4 import BeautifulSoup
from odoo import api, fields, models, _


class CRMDynamicFields(models.TransientModel):
    """Creating new transient model for the wizard from"""
    _name = 'crm.dynamic.fields'
    _description = 'CRM Dynamic Fields'
    _inherit = ['ir.model.fields']

    form_view_id = fields.Many2one('ir.ui.view', string="Form View ID",
                                   help="Select the view to be used as"
                                        "the form view for this field.")

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than
                 'one2many' and 'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    def set_domain(self):
        """Return the fields that are currently present in the form"""
        view_id = self.env.ref('crm.crm_lead_view_form')
        view_arch = str(view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list_1 = [tag.attrib['name'] for tag in doc.findall('.//field')
                        if 'invisible' not in tag.attrib and 'attrs'
                        not in tag.attrib]
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'crm.lead')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', field_list_1)]

    def _set_default(self):
        """setting the default model"""
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'crm.lead')])
        return [('id', '=', model_id.id)]

    position_field_id = fields.Many2one('ir.model.fields',
                                        string='Field Name',
                                        domain=set_domain, required=True,
                                        help="Select the field that will "
                                             "determine the position of"
                                             " the custom field.")
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')],
                                string='Position in Backend',
                                required=True, help="Position of field")
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True,
                               index=True, ondelete='cascade',
                               help="The models this field belongs to",
                               domain=_set_default)
    ref_model_id = fields.Many2one('ir.model', string='Model',
                                   index=True,
                                   help="This field is used to specify the "
                                        "model that the dynamic field will be "
                                        "associated with.")
    selection_field = fields.Char(string="Selection Options",
                                  help='Enter selection value')
    rel_field_id = fields.Many2one('ir.model.fields',
                                   string='Related Field',
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
    widget_id = fields.Many2one('crm.field.widgets', string='Widget',
                                help='Select widget')
    # Already existing field.
    groups = fields.Many2many('res.groups',
                              'product_dynamic_fields_group_rel',
                              'field_id', 'group_id',
                              help='The security groups that have access to '
                                   'this dynamic field.')
    extra_features = fields.Boolean(string="Show Extra Properties",
                                    help="A boolean field that determines "
                                         "whether to display extra properties "
                                         "for this dynamic field in the user "
                                         "interface")

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
             'is_dynamic': True
             })
        inherit_id = self.env.ref('crm.crm_lead_view_form')
        view_id = self.env.ref('crm.crm_lead_view_form')
        view_arch = str(view_id.arch_base)
        soup = BeautifulSoup(view_arch, 'html.parser')
        fields_all = soup.find_all('field',
                                   attrs={"name": self.position_field_id.name})
        for field in fields_all:
            if field.parent.name == "div":
                parent_div = field.parent
                class_name_string = ' '.join(parent_div['class'])
                if self.position == 'before':
                    if self.widget_id:
                        arch_base = _('<?xml version="1.0"?>'
                                      '<data>'
                                      '<label for="{}" position="{}">'
                                      '<field name="{}" widget="{}"/>'
                                      '</label>'
                                      '</data>').format(
                            self.position_field_id.name, self.position,
                            self.name,
                            self.widget_id.name)
                    else:
                        arch_base = ('<?xml version="1.0"?>'
                                     '<data>'
                                     '<label for="{}" position="{}">'
                                     '<field name="{}"/>'
                                     '</label>'
                                     '</data>').format(
                            self.position_field_id.name,
                            self.position, self.name)
                else:
                    if self.widget_id:
                        arch_base = _('<?xml version="1.0"?>'
                                      '<data>'
                                      '<div class="{}" position="{}">'
                                      '<field name="{}" widget="{}"/>'
                                      '</div>'
                                      '</data>').format(
                            class_name_string, self.position,
                            self.name,
                            self.widget_id.name)
                    else:
                        arch_base = ('<?xml version="1.0"?>'
                                     '<data>'
                                     '<div class="{}" position="{}">'
                                     '<field name="{}"/>'
                                     '</div>'
                                     '</data>').format(class_name_string,
                                                       self.position,
                                                       self.name)
            else:
                arch_base = _('<?xml version="1.0"?>'
                              '<data>'
                              '<field name="%s" position="%s">'
                              '<field name="%s"/>'
                              '</field>'
                              '</data>') % (
                                self.position_field_id.name, self.position,
                                self.name)
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
            if self.position_field_id.name == 'partner_id':
                arch_base = (
                    f"""<xpath expr="//group[@name='opportunity_partner']/field
                    [@name='{self.position_field_id.name}']" position=
                    "{self.position}"><field name="{self.name}"/></xpath>""")
                if self.widget_id:
                    arch_base = (
                        f"""<xpath expr="//group[@name='opportunity_partner']
                        /field[@name='{self.position_field_id.name}']" 
                        position="{self.position}"><field name="{self.name}" 
                        widget="{self.widget_id.name}"/></xpath>""")
            self.form_view_id = self.env['ir.ui.view'].sudo().create(
                {
                    'name': 'crm.dynamic.fields',
                    'type': 'form',
                    'model': 'crm.lead',
                    'mode': 'extension',
                    'inherit_id': inherit_id.id,
                    'arch_base': arch_base,
                    'active': True,
                })
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

    @api.depends('field_type')
    @api.onchange('field_type')
    def onchange_field_type(self):
        """ This method is triggered when the field_type field is changed.
            It updates the domain of the widget field based on the
            selected field_type."""
        if self.field_type:
            if self.field_type == 'binary':
                return {'domain': {'widget_id': [('name', '=', 'image')]}}
            elif self.field_type == 'many2many':
                return {'domain': {
                    'widget_id': [
                        ('name', 'in', ['many2many_tags', 'binary'])]}}
            elif self.field_type == 'selection':
                return {'domain': {
                    'widget_id': [('name', 'in', ['radio', 'priority'])]}}
            elif self.field_type == 'float':
                return {'domain': {'widget_id': [('name', '=', 'monetary')]}}
            elif self.field_type == 'many2one':
                return {'domain': {'widget_id': [('name', '=', 'selection')]}}
            elif self.field_type == 'Boolean':
                return {'domain': {'widget_id': [('name', '=', 'checkbox')]}}
            else:
                return {'domain': {'widget_id': [('id', '=', False)]}}
        return {'domain': {'widget_id': [('id', '=', False)]}}

    def unlink(self):
        """Overrides the default 'unlink' method of the
        'CRMDynamicFields' model to perform custom deletion logic."""
        if self.form_view_id:
            self.form_view_id.active = False
            for field in self:
                if field.ttype == 'many2many':
                    field: [(5, 0, 0)]
                else:
                    query = """delete FROM ir_model_fields WHERE name = %s"""
                    self.env.cr.execute(query, [field.name])
        return super(CRMDynamicFields, self).unlink()
