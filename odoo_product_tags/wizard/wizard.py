# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
import datetime


class ProductTagsWizard(models.TransientModel):
    _name = 'product.tags.wizard'
    _description = 'Product Tags Wizard'

    product_tags_ids = fields.Many2many(
        "product.tags", string="Product Tags", help="Product Tags")

    product_ids = fields.Many2many(
        'product.template', string="Products", readonly=True)

    def action_apply_product_tags(self):
        product_id = self.env['product.template'].sudo().browse(
            self.env.context.get('active_ids'))
        pro_tag_ids = self.product_tags_ids.ids
        for product in product_id:
            product.update({
                "product_tags_ids": [(6, 0, pro_tag_ids)],
            })

