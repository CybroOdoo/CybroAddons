# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
############################################################################
from odoo import api, exceptions, fields, models


class WebsiteSeoAttribute(models.Model):
    """This module allows to user to give attributes"""
    _name = 'website.seo.attributes'
    _description = 'Website SEO'

    name = fields.Char(string='Name', required=True, help='Name')
    product = fields.Selection([('name', 'Product Name'),
                                ('description', 'Description for Quotations'),
                                ('description_sale', 'Product Description'),
                                ('default_code', 'Internal Reference'),
                                ('company_id', 'Company Name')],
                               help='Select Product', string="Product")
    models = fields.Selection([('product', 'Product'),
                               ('product_category', 'Product Category')],
                              string='Model', help='Choose your model')
    category = fields.Selection([('name', 'Category Name'),
                                 ('parent_id', 'Category Parent Name'),
                                 ('category_description',
                                  'Category Description')],
                                help='Select Product Category',
                                string="Select Product Category")

    @api.constrains('name')
    def _check_unique_name(self):
        """Check for unique name"""
        for record in self:
            domain = [('name', '=', record.name.lower())]
            if self.search_count(domain) > 1:
                raise exceptions.ValidationError("Name must be unique.")
