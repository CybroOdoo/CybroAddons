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
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError


class SaleOrderDynamicFields(models.TransientModel):
    """ For adding custom fields in 'sale.order'."""
    _name = 'sale.order.dynamic.field'
    _description = 'Sale Order Dynamic Fields'

    position_field = fields.Many2one(
        'ir.model.fields', string='Field Name',
        domain=lambda self: self.set_domain(), required=True,
        help="The custom field is added before or after this field")
    position = fields.Selection(
        [('before', 'Before'), ('after', 'After')],
        string='Position',
        required=True,
        help="Before/After")
    model_id = fields.Many2one(
        'ir.model', string='Model',
        required=True, index=True, ondelete='cascade',
        default=lambda self: self.env['ir.model'].search([('model', '=', 'sale.order')], limit=1),
        domain=lambda self: self._set_default(),
        help="The model this field belongs to")
    model = fields.Char(
        related='model_id.model', string='Model Name', readonly=True)
    ref_model_id = fields.Many2one(
        'ir.model', string='Reference Model', index=True,
        help="Reference model for Many2one and Many2many field types")
    selection_field = fields.Char(string="Selection Options",
                                  help="Field type Selection")
    name = fields.Char(string='Technical Name', required=True)
    field_description = fields.Char(string='Field Label', required=True, translate=True)
    field_type = fields.Selection(
        selection='get_possible_field_types', string='Field Type',
        required=True, help="Type of field")
    state = fields.Selection([
        ('manual', 'Custom Field'),
        ('base', 'Base Field'),
    ], default='manual', string='State', readonly=True)
    required = fields.Boolean(string='Required')
    index = fields.Boolean(string='Indexed')
    store = fields.Boolean(string='Stored', default=True)
    help = fields.Char(string='Help', translate=True)
    readonly = fields.Boolean(string='Read Only')
    copied = fields.Boolean(string='Copied')
    widget = fields.Many2one(
        'field.widget', string='Widget',
        domain="[('data_type', '=', field_type)]",
        help="Widget for the field type")
    extra_features = fields.Boolean(
        string="Show Extra Properties", help="Extra properties for field")

    @api.model
    def get_possible_field_types(self):
        """
        Return supported field types for dynamic field creation.
        """
        return [
            ('binary', 'Binary'),
            ('boolean', 'Boolean'),
            ('char', 'Char'),
            ('date', 'Date'),
            ('datetime', 'Datetime'),
            ('float', 'Float'),
            ('html', 'Html'),
            ('integer', 'Integer'),
            ('many2many', 'Many2many'),
            ('many2one', 'Many2one'),
            ('monetary', 'Monetary'),
            ('selection', 'Selection'),
            ('text', 'Text'),
        ]

    def set_domain(self):
        """ Return the fields that currently present in the form."""
        view_id = self.env.ref('sale.view_order_form')
        view_arch = str(view_id.arch_base)
        doc = xee.fromstring(view_arch)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        model_id = self.env['ir.model'].sudo().search([
            ('model', '=', 'sale.order')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'),
                ('name', 'in', field_list)]

    def _set_default(self):
        """ Set default model for dynamically created fields."""
        model_id = self.env['ir.model'].sudo().search([
            ('model', '=', 'sale.order')])
        return [('id', '=', model_id.id)]

    @api.onchange('field_type')
    def _onchange_field_type(self):
        """Reset widget if incompatible with selected field_type."""
        if self.widget and self.widget.data_type != self.field_type:
            self.widget = False

    @api.onchange('widget')
    def _onchange_widget(self):
        """
        Checking the selected model 'ir.attachment' for many2many_binary widget.
        """
        if self.widget and self.widget.name == 'many2many_binary':
            self.ref_model_id = self.env.ref('base.model_ir_attachment')

    @api.onchange('ref_model_id')
    def _onchange_ref_model_id(self):
        """
        Raise a warning if the wrong model is chosen for the 'many2many_binary'
        widget.
        """
        if (self.widget and self.widget.name == 'many2many_binary' and
                self.ref_model_id and self.ref_model_id.model != 'ir.attachment'):
            self.ref_model_id = self.env.ref('base.model_ir_attachment')
            raise UserError(
                _('This widget is only available for model Attachment'))

    def create_fields(self):
        """Create custom field and inherited view for sale.order."""
        self.ensure_one()
        if not self.env.user.has_group('dynamic_sale_order_fields.group_add_sale_custom_fields'):
            raise AccessError(_('You are not allowed to create custom fields in Sale.'))

        if not self.model_id or self.model_id.model != 'sale.order':
            raise UserError(_("Custom fields can only be created for the 'sale.order' model."))

        if (not self.position_field or self.position_field.model != 'sale.order'
                or self.position_field.state != 'base'):
            raise UserError(_('Select a standard sale order field for positioning.'))

        self.env['ir.model.fields'].sudo().create({
            'name': self.name,
            'field_description': self.field_description,
            'model_id': self.model_id.id,
            'ttype': self.field_type,
            'relation': self.ref_model_id.model if self.ref_model_id else False,
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
        data = xee.Element('data')
        field = xee.SubElement(data, 'field', {
            'name': self.position_field.name,
            'position': self.position,
        })
        field_attrs = {'name': self.name}
        if self.widget:
            field_attrs['widget'] = self.widget.name
        xee.SubElement(field, 'field', field_attrs)
        arch_base = xee.tostring(data, encoding='unicode')
        self.env['ir.ui.view'].sudo().create({
            'name': 'sale.order.dynamic.field',
            'type': 'form',
            'model': 'sale.order',
            'mode': 'extension',
            'inherit_id': inherit_id.id,
            'arch_base': arch_base,
            'active': True
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
