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
from odoo import models, fields


class ProductCategory(models.Model):
    """ Inheriting product category to add fields for publish
    product in website """
    _inherit = 'product.category'

    published_count = fields.Integer(string="Published",
                                     compute='_compute_published_count',
                                     help='Total count of published product '
                                          'in website.')
    unpublished_count = fields.Integer(string="Unpublished",
                                       compute='_compute_published_count',
                                       help='Total count of unpublished '
                                            'product in website.')
    def _compute_published_count(self):
        """Function for computing count of published and unpublished products"""
        for rec in self:
            products = self.env['product.template'].search(
                [('categ_id', 'child_of', rec.id), ('sale_ok', '=', True)])
            rec.published_count = len(products.filtered('is_published'))
            rec.unpublished_count = len(products.filtered(lambda p: not p.is_published))

    def action_publish_all_products(self):
        """Smart tab function to publish products in website"""
        for rec in self:
            products = self.env['product.template'].search(
                [('categ_id', 'child_of', rec.id), ('sale_ok', '=', True), ('is_published', '=', False)])
            products.write({'is_published': True})

    def action_unpublish_all_products(self):
        """Smart tab function to unpublish products in website"""
        for rec in self:
            products = self.env['product.template'].search(
                [('categ_id', 'child_of', rec.id), ('sale_ok', '=', True), ('is_published', '=', True)])
            products.write({'is_published': False})

    def action_view_published_products(self):
        """Open a list of published products belonging to this category."""
        return {
            'name': 'Published Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('categ_id', 'child_of', self.id),
                ('sale_ok', '=', True),
                ('is_published', '=', True),
            ],
        }

    def action_view_unpublished_products(self):
        """Open a list of unpublished products belonging to this category."""
        return {
            'name': 'Unpublished Products',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [
                ('categ_id', 'child_of', self.id),
                ('sale_ok', '=', True),
                ('is_published', '=', False),
            ],
        }
