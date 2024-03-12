# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
import xml.etree.ElementTree as xee
from odoo import api, fields, models, _


class SaleOrderDynamicFields(models.TransientModel):
    """It inherits ir.model.fields."""
    _name = 'sale.order.dynamic.fields'
    _description = 'Dynamic Fields'
    _inherit = 'ir.model.fields'

    @api.model
    def get_possible_field_types(self):
        """Return all available field types
        other than 'one2many' and 'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    def set_domain(self):
        """Return the fields that currently present in the form"""
        view_arch = str(self.env.ref('sale.view_order_form').arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'sale.order')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', field_list)]

    def _set_default(self):
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'sale.order')])
        return [('id', '=', model_id.id)]

    def action_create_fields(self):
        """Create custom fields in the 'sale.order' model and update the view
           accordingly.
           This function creates custom fields based on the provided parameters
            and extends the 'sale.order' form view to display these fields.

           Returns:
               dict: Dictionary specifying the action to be taken after field
               creation (e.g., reload the view).
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
             'is_dynamic': True
             })
        inherit_id = self.env.ref('sale.view_order_form')
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
                          '<field name="%s" widget_id="%s"/>'
                          '</field>'
                          '</data>') % (self.position_field_id.name,
                                        self.position, self.name,
                                        self.widget_id.name)
        self.env['ir.ui.view'].sudo().create(
            {'name': 'sale.order.dynamic.fields',
             'type': 'form',
             'model': 'sale.order',
             'mode': 'extension',
             'inherit_id': inherit_id.id,
             'arch_base': arch_base,
             'active': True})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    position_field_id = fields.Many2one(
        'ir.model.fields', string='Field Name', domain=set_domain,
        required=True, help='Field Name')
    position = fields.Selection(
        [('before', 'Before'), ('after', 'After')], string='Position',
        required=True, help='Position')
    model_id = fields.Many2one(
        'ir.model', string='Model', required=True, index=True,
        ondelete='cascade',
        help="The model this field belongs to", domain=_set_default)
    ref_model_id = fields.Many2one(
        'ir.model', string='Model', help='Model', index=True)
    selection_field = fields.Char(string="Selection Options",
                                  help="Selection Options")
    related_field_id = fields.Many2one(
        'ir.model.fields', string='Related Field', help='Related Field')
    field_type = fields.Selection(
        selection='get_possible_field_types', string='Field Type',
        required=True, help='Field Type')
    ttype = fields.Selection(string="Field Type", help='Field Type',
                             related='field_type')
    widget_id = fields.Many2one(
        'field.widget', string='Widget', help='Widget')
    groups = fields.Many2many(
        'res.groups', 'sale_dynamic_fields_groups_rel',
        'field_id', 'group_id', string="Groups", help='Groups')
    extra_features = fields.Boolean(string="Show Extra Properties",
                                    help="Show Extra Properties")

    @api.onchange('field_type')
    def _onchange_field_type(self):
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
