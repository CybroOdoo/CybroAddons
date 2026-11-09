# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import xml.etree.ElementTree as xee
from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


class ProductDynamicField(models.TransientModel):
    """ For adding custom fields in product form."""
    _name = 'product.dynamic.fields'
    _description = 'Dynamic Fields'
    _inherit = 'ir.model.fields'

    position_field = fields.Many2one(
        'ir.model.fields',
        domain=lambda self: self.set_domain(),
        required=True,
        help="The custom field is added before or after this field")
    position = fields.Selection(
        [('before', 'Before'), ('after', 'After')],
        required=True,
        help="Before/After")
    model_id = fields.Many2one(
        'ir.model',
        required=True,
        index=True,
        ondelete='cascade',
        domain=lambda self: self._get_model_domain(),
        default=lambda self: self.env['ir.model'].sudo().search([('model', '=', 'product.template')], limit=1),
        help="The model this field belongs to")
    ref_model_id = fields.Many2one(
        'ir.model',
        string='Reference Model',
        index=True,
        help="Reference model for Many2one and Many2many field types")
    selection_field = fields.Char(
        string="Selection Values",
        help="Field type Selection")
    field_type = fields.Selection(
        selection='get_possible_field_types',
        required=True,
        help="Type of field")
    ttype = fields.Selection(
        related='field_type',
        help="Type of field")
    widget = fields.Many2one(
        'field.widget',
        domain=lambda self: "[('data_type', '=', field_type)]",
        help="Widget for the field type")
    groups = fields.Many2many(
        'res.groups',
        'product_dynamic_fields_group_rel',
        'field_id', 'group_id',
        help="User group allows this operation")
    extra_features = fields.Boolean(
        string="Show Extra Properties",
        help="Extra properties for field")

    @api.onchange('widget')
    def _onchange_widget(self):
        """ Checking the selected model 'ir.attachment' for many2many_binary
        widget."""
        if self.widget.name == 'many2many_binary':
            self.ref_model_id = self.env.ref('base.model_ir_attachment')

    @api.onchange('ref_model_id')
    def _onchange_ref_model_id(self):
        """ Return a warning if the wrong model is chosen for the
        'many2many_binary' widget."""
        if (self.widget.name == 'many2many_binary' and
                self.ref_model_id.name != 'Attachment'):
            self.ref_model_id = self.env.ref('base.model_ir_attachment')
            return {
                'warning': {
                    'title': self.env._('Invalid Model'),
                    'message': self.env._('This widget is only available for model Attachment'),
                }
            }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name') and not vals['name'].startswith('x_'):
                vals['name'] = f"x_{vals['name']}"
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('name') and not vals['name'].startswith('x_'):
            vals['name'] = f"x_{vals['name']}"
        return super().write(vals)

    @api.model
    def get_possible_field_types(self):
        """ Return all available field types other than 'one2many' and
        'reference' fields."""
        field_types = [
            'char',
            'text',
            'integer',
            'float',
            'boolean',
            'date',
            'datetime',
            'binary',
            'selection',
            'many2one',
            'many2many',
        ]

        return [(ft, ft) for ft in sorted(field_types)]

    def set_domain(self):
        """ Return the fields that are currently present in the form."""
        view_id = self.env.ref('product.product_template_only_form_view')
        view_arch = str(view_id.arch_base or view_id.arch or '')
        field_list = []
        if view_arch:
            doc = xee.fromstring(view_arch)
            for tag in doc.findall('.//field'):
                name = tag.attrib.get('name')
                if name:
                    field_list.append(name)
        model_id = self.env['ir.model'].sudo().search([
            ('model', '=', 'product.template')], limit=1)
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', field_list)]

    def _get_model_domain(self):
        """ Set default model domain for dynamically created fields."""
        model_id = self.env['ir.model'].sudo().search([
            ('model', '=', 'product.template')], limit=1)
        return [('id', '=', model_id.id)]

    def create_fields(self):
        """ Create custom fields."""
        if not self.env.user.has_group('dynamic_product_fields.dynamic_product_fields_user'):
            raise AccessError(self.env._("You do not have permission to create custom fields."))

        product_model = self.env['ir.model'].sudo().search([
            ('model', '=', 'product.template')
        ], limit=1)
        if not self.model_id or self.model_id != product_model:
            raise UserError(self.env._("Custom fields can only be created for the Product model."))

        raw_name = self.name or ''
        field_name = raw_name if raw_name.startswith('x_') else f'x_{raw_name}'
        self.env['ir.model.fields'].sudo().create({
            'name': field_name,
            'field_description': self.field_description,
            'model_id': product_model.id,
            'ttype': self.field_type,
            'relation': self.ref_model_id.model if self.ref_model_id else False,
            'required': self.required,
            'index': self.index,
            'store': self.store,
            'help': self.help,
            'readonly': self.readonly,
            'selection': self.selection_field if self.field_type == 'selection' else False,
            'copied': self.copied,
            'is_dynamic': True,
        })
        inherit_id = self.env.ref('product.product_template_only_form_view')

        data_elem = xee.Element('data')
        pos_elem = xee.SubElement(data_elem, 'field', {
            'name': self.position_field.name,
            'position': self.position,
        })
        new_field_attrs = {'name': field_name}
        if self.widget and self.widget.name:
            new_field_attrs['widget'] = self.widget.name
        xee.SubElement(pos_elem, 'field', new_field_attrs)
        arch_base = f'<?xml version="1.0"?>\n{xee.tostring(data_elem, encoding="unicode")}'

        self.env['ir.ui.view'].sudo().create({
            'name': f'product.template.dynamic.{field_name}',
            'type': 'form',
            'model': 'product.template',
            'mode': 'extension',
            'inherit_id': inherit_id.id,
            'arch_base': arch_base,
            'active': True,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
