# -*- coding: utf-8 -*-

import xml.etree.ElementTree as xee

from odoo import api, models, fields, _


class EmployeeDynamicFields(models.TransientModel):
    _name = 'wizard.dynamic.fields'
    _description = 'Dynamic Fields'
    _inherit = 'ir.model.fields'

    @api.model
    def get_field_types(self):
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        return field_list

    @api.multi
    def set_domain(self):
        view_id = self.env.ref('hr.view_employee_form')
        data1 = str(view_id.arch_base)
        doc = xee.fromstring(data1)
        field_list = []
        for tag in doc.findall('.//field'):
            field_list.append(tag.attrib['name'])
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'hr.employee')])
        return [('model_id', '=', model_id.id), ('state', '=', 'base'), ('name', 'in', field_list)]

    @api.multi
    def _set_default(self):
        model_id = self.env['ir.model'].sudo().search([('model', '=', 'hr.employee')])
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
        inherit_id = self.env.ref('hr.view_employee_form')
        arch_base = _('<?xml version="1.0"?>'
                      '<data>'
                      '<field name="%s" position="%s">'
                      '<field name="%s"/>'
                      '</field>'
                      '</data>') % (self.position_field.name, self.position, self.name)
        self.env['ir.ui.view'].sudo().create({'name': 'hr.employee.dynamic.fields',
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

    position_field = fields.Many2one('ir.model.fields', string='Field Name',
                                     domain=set_domain, required=True)
    position = fields.Selection([('before', 'Before'),
                                 ('after', 'After')], string='Position', required=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, index=True, ondelete='cascade',
                               help="The model this field belongs to", domain=_set_default)
    ref_model_id = fields.Many2one('ir.model', string='Model', index=True)
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')
    ttype = fields.Selection(selection='get_field_types', string='Field Type', required=True)
