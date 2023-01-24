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
import ast


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_tags_ids = fields.Many2many(
        "product.tags", string="Product Tags", help="Product Tags")

    @api.model
    def create(self, vals):
        """Inherited for passing the product Tags."""
        res = super(ProductTemplate, self).create(vals)
        if not res.product_tags_ids:
            pro_tag = self.env['ir.config_parameter'].sudo().get_param(
                'odoo_product_tags.product_tags_ids')
            if pro_tag:
                tag_ids = ast.literal_eval(pro_tag)
                res.update({
                    "product_tags_ids": [(6, 0, tag_ids)],
                })

            return res
        else:
            return res

    def action_apply_tags(self):
        return {
            'name': 'Apply Product Tag',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.tags.wizard',
            'context': {
                'default_product_ids': self.ids,
            },
            'target': 'new',
        }

