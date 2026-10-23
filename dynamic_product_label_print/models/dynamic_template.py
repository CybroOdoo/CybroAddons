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


class DynamicTemplate(models.Model):
    """Dynamic template for Products"""
    _name = "dynamic.template"
    _description = 'Dynamic Template'

    name = fields.Char(
        string='Name', required=True, help='Name of the template'
    )
    bc_height = fields.Integer(
        string='Barcode Height',
        required=True,
        default=15,
        help='Height of the barcode in mm',
    )
    bc_width = fields.Integer(
        string='Barcode Width',
        required=True,
        default=30,
        help='Width of the barcode in mm',
    )
    dynamic_field_ids = fields.One2many(
        'dynamic.fields',
        'template_id',
        string='Fields',
        help='Select the required fields from the product with desired '
             'size and color for the label report',
    )
