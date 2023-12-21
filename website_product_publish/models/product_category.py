# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Ayana K P (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models, fields


class ProductCategory(models.Model):
    """ Inheriting product category to add fields for publish
    product in website """
    _inherit = 'product.category'

    published_count = fields.Integer(string="Published",
                                     compute='_compute_count',
                                     help='Total count of published product '
                                          'in website')
    unpublished_count = fields.Integer(string="Unpublished",
                                       compute='_compute_count',
                                       help='Total count of unpublished '
                                            'product in website')

    def _compute_count(self):
        """Function for computing count of published and unpublished products"""
        for rec in self:
            products = self.env['product.template'].search(
                [('categ_id', '=', rec.id)])
            rec.published_count = len(products.filtered(lambda
                                                            product: product.is_published == True and product.sale_ok == True))
            rec.unpublished_count = len(products.filtered(lambda
                                                              product: product.is_published == False and product.sale_ok == True))

    def action_publish_all_products(self):
        """Smart tab function to publish products in website"""
        for rec in self:
            for product in self.env['product.template'].search(
                    [('categ_id', '=', rec.id)]).filtered(
                lambda product: product.sale_ok == True):
                if not product.is_published:
                    product.is_published = True

    def action_nothing(self):
        """ return true """
        return True
