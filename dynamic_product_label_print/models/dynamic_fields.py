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
from odoo import fields, models


class DynamicFields(models.Model):
    """One2many fields of dynamic template"""
    _name = "dynamic.fields"
    _description = "Dynamic Fields"

    def set_domain(self):
        """Fields of the product model"""
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', 'product.product')]
        )
        return [
            ('model_id', '=', model_id.id),
            ('state', '=', 'base'),
            ('name', 'in', ['name', 'categ_id', 'type', 'list_price']),
        ]

    size = fields.Char(string='Font Size', help="Set the size of the field")
    color = fields.Char(
        string='Font Color', help="Set the colour of the field"
    )
    fd_name_id = fields.Many2one(
        'ir.model.fields',
        string='Field Name',
        domain=set_domain,
        help='Name of the field',
    )
    field_type = fields.Selection(
        string='Field Type',
        related='fd_name_id.ttype',
        help='Type of the field name',
    )
    template_id = fields.Many2one(
        'dynamic.template',
        string='Template',
        help='Relation to dynamic template',
    )
