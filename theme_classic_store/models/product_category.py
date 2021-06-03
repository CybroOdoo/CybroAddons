# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    category_count = fields.Integer("Count", compute="_compute_category_count")

    def _compute_category_count(self):
        for ct in self:
            product_ids = self.env['product.template'].search(
                [('website_published', '=', True)])
            count = 0
            for rec in product_ids:
                for cat in rec.public_categ_ids:
                    if cat in ct:
                        count += 1
            ct.category_count = count


class Product(models.Model):
    _inherit = 'product.template'

    views = fields.Integer('Views')
    most_viewed = fields.Boolean('Most Viewed')
