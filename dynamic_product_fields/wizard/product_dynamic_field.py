# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Aysha Shalin (odoo@cybrosys.com)
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
###############################################################################
import xml.etree.ElementTree as xee
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductDynamicField(models.TransientModel):
    """ For adding custom fields in product form."""
    _name = 'product.dynamic.field'
    _description = 'Dynamic Fields'
    _inherit = 'ir.model.fields'

    @api.model
    def get_possible_field_types(self):
        """ Return all available field types other than 'one2many' and
        'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    def set_domain(self):
        """ Return the fields that are currently present in the form."""
        view_id = self.env.ref('product.product_template_only_form_view')
        view_arch = str(view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        model_id = self.env['ir.model'].sudo().search([
            ('model', '=', 'product.template')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', field_list)]

    def _set_default(self):
        """ Set default model for dynamically created fields."""
        model_id = self.env['ir.model'].sudo().search([
            ('model', '=', 'product.template')])
        return [('id', '=', model_id.id)]

    def create_fields(self):
        """ Create custom fields."""
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
            'is_dynamic': True,
        })
        inherit_id = self.env.ref('product.product_template_only_form_view')
        arch_base = _('<?xml version="1.0"?>'
                      '<data>'
                      '<field name="%s" position="%s">'
                      '<field name="%s"/>'
                      '</field>'
                      '</data>') % (self.position_field.name, self.position,
                                    self.name)
        if self.widget:
            arch_base = _('<?xml version="1.0"?>'
                          '<data>'
                          '<field name="%s" position="%s">'
                          '<field name="%s" widget="%s"/>'
                          '</field>'
                          '</data>') % (self.position_field.name, self.position,
                                        self.name, self.widget.name)
        self.env['ir.ui.view'].sudo().create({
            'name': 'product.dynamic.field',
            'type': 'form',
            'model': 'product.template',
            'mode': 'extension',
            'inherit_id': inherit_id.id,
            'arch_base': arch_base,
            'active': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    position_field = fields.Many2one(
        'ir.model.fields',
        string='Field Name',
        domain=set_domain, required=True,
        help="The custom field is added before or after this field")
    position = fields.Selection(
        [('before', 'Before'), ('after', 'After')],
        string='Position',
        required=True,
        help="Before/After")
    model_id = fields.Many2one('ir.model', string='Model',
                               required=True, index=True, ondelete='cascade',
                               domain=_set_default,
                               help="The model this field belongs to")
    ref_model_id = fields.Many2one(
        'ir.model', string='Model',
        index=True,
        help="Reference model for Many2one and Many2many field types")
    selection_field = fields.Char(string="Selection Options",
                                  help="Field type Selection")
    field_type = fields.Selection(selection='get_possible_field_types',
                                  string='Field Type', required=True,
                                  help="Type of field")
    ttype = fields.Selection(string="Field Type",
                             related='field_type',
                             help="Type of field")
    widget = fields.Many2one(
        'field.widget',
        string='Widget',
        domain=lambda self: "[('data_type', '=', field_type)]",
        help="Widget for the field type")
    groups = fields.Many2many(
        'res.groups',
        'product_dynamic_fields_group_rel',
        'field_id', 'group_id',
        help="User group allows this operation")
    extra_features = fields.Boolean(string="Show Extra Properties",
                                    help="Extra properties for field")

    @api.onchange('widget')
    def _onchange_widget(self):
        """ Checking the selected model 'ir.attachment' for many2many_binary
        widget."""
        if self.widget.name == 'many2many_binary':
            self.ref_model_id = self.env.ref('base.model_ir_attachment')

    @api.onchange('ref_model_id')
    def _onchange_ref_model_id(self):
        """ Raise a warning if the wrong model is chosen for the
        'many2many_binary' widget."""
        if (self.widget.name == 'many2many_binary' and
                self.ref_model_id.name != 'Attachment'):
            self.ref_model_id = self.env.ref('base.model_ir_attachment')
            raise UserError(
                'This widget is only available for model Attachment')
