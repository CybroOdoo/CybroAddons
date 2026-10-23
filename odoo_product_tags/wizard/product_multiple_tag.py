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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import Command, fields, models


class ProductMultipleTag(models.TransientModel):
    """Model to add multiple product tags."""
    _name = 'product.multiple.tag'
    _description = 'Product Multiple Tag'

    is_product = fields.Boolean(default=False, help='Is Product')
    is_product_template = fields.Boolean(default=False, help='Is Product Template')
    product_tag_ids = fields.Many2many(
        "product.tag", string="Product Tags", help="Product Tags")
    product_ids = fields.Many2many(
        'product.product', string="Product Variants", readonly=True,
        help='The product Variants')
    product_tmp_ids = fields.Many2many(
        'product.template', string="Product Templates", readonly=True,
        help='The product templates.')

    def action_apply_template_tags(self):
        """Applying product tag to Template"""
        active_ids = self.env.context.get('active_ids')
        templates = self.env['product.template'].browse(active_ids) if active_ids else self.product_tmp_ids
        if templates:
            templates.write({
                "product_tag_ids": [Command.set(self.product_tag_ids.ids)],
            })

    def action_apply_product_tags(self):
        """Applying product tag to Product"""
        active_ids = self.env.context.get('active_ids')
        products = self.env['product.product'].browse(active_ids) if active_ids else self.product_ids
        if products:
            products.write({
                "product_tag_ids": [Command.set(self.product_tag_ids.ids)],
            })


