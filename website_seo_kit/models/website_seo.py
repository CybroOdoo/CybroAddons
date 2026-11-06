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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class WebsiteSeoAttribute(models.Model):
    """Attributes that can be used to build the SEO meta content"""
    _name = 'website.seo.attributes'
    _description = 'Website SEO Attribute'

    name = fields.Char(required=True, help='Name of the SEO attribute')
    product = fields.Selection(
        [('name', 'Product Name'),
         ('description', 'Description for Quotations'),
         ('description_sale', 'Product Description'),
         ('default_code', 'Internal Reference'),
         ('company_id', 'Company Name')],
        help='Product field used by this attribute')
    models = fields.Selection(
        [('product', 'Product'),
         ('product_category', 'Product Category')],
        string='Model', help='Model this attribute belongs to')
    category = fields.Selection(
        [('name', 'Category Name'),
         ('parent_id', 'Category Parent Name'),
         ('category_description', 'Category Description')],
        string='Select Product Category',
        help='Product category field used by this attribute')

    @api.constrains('name')
    def _check_unique_name(self):
        """Ensure the attribute name is unique (case-insensitive)"""
        for record in self:
            # Escape the wildcards, so the name is matched literally.
            name = (record.name or '').replace('\\', '\\\\').replace(
                '%', '\\%').replace('_', '\\_')
            domain = [('id', '!=', record.id), ('name', '=ilike', name)]
            if self.search_count(domain):
                raise ValidationError(
                    self.env._("Name must be unique."))
