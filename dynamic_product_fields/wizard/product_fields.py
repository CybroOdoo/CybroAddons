# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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

import xml.etree.ElementTree as xee
from odoo import api, models, fields, _


class ProductDynamicFields(models.TransientModel):
    _name = 'product.dynamic.fields'
    _description = 'Dynamic Fields'
    _inherit = 'ir.model.fields'

    @api.model
    def get_possible_field_types(self):
        """Return all available field types other than 'one2many' and 'reference' fields."""
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    @api.multi
    def set_domain(self):
        """Return the fields that currently present in the form"""
        view_id = self.env.ref('product.product_template_only_form_view')
        view_arch = str(view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.template')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'), ('name', 'in', field_list)]

    @api.multi
    def _set_default(self):
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.template')])
        return [('id', '=', model_id.id)]

    @api.multi
    def create_fields(self):
        self.env['ir.model.fields'].sudo().create({'name': self.name,
                                                   'field_description': self.field_description,
                                                   'model_id': self.model_id.id,
                                                   'ttype': self.ttype,
                                                   'relation': self.ref_model_id.model,
                                                   'required': self.required,
                                                   'selection': self.selection,
                                                   'copy': self.copy,
                                                   'active': True})
        inherit_id = self.env.ref('product.product_template_only_form_view')
        arch_base = _('<?xml version="1.0"?>'
                      '<data>'
                      '<field name="%s" position="%s">'
                      '<field name="%s"/>'
                      '</field>'
                      '</data>') % (self.position_field.name, self.position, self.name)
        self.env['ir.ui.view'].sudo().create({'name': 'product.dynamic.fields',
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

    position_field = fields.Many2one('ir.model.fields', string='Field Name',
                                     domain=set_domain, required=True)
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')], string='Position', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, index=True, ondelete='cascade',
                               help="The model this field belongs to", domain=_set_default)
    ref_model_id = fields.Many2one('ir.model', string='Model', index=True)
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')
    ttype = fields.Selection(selection='get_possible_field_types', string='Field Type', required=True)
