# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import models, fields, api

class ProductTemplate(models.Model):
    """
    Inherited Product Template model for the Kids Care theme.
    Automatically synchronizes public categories based on the internal
    category assignment to ensure consistency between the backend and website.
    """
    _inherit = 'product.template'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the default create method to trigger public category
        synchronization for newly created products.
        """
        products = super(ProductTemplate, self).create(vals_list)
        for product in products:
            product._sync_public_categories()
        return products

    def write(self, vals):
        """
        Overrides the default write method to re-sync public categories
        whenever the internal category (categ_id) is updated.
        """
        res = super(ProductTemplate, self).write(vals)
        if 'categ_id' in vals:
            for product in self:
                product._sync_public_categories()
        return res

    def _sync_public_categories(self):
        """
        Automatically assign public categories based on internal category name.
        Maps internal categories like 'BABY FEEDING' to their corresponding
        website public categories.
        """
        if not self.categ_id:
            return
        category_mapping = {
            'BABY FEEDING': 'theme_kids_care.public_category_baby_feeding',
            'BABY T-SHIRT': 'theme_kids_care.public_category_baby_tshirt',
            'BABY TOYS': 'theme_kids_care.public_category_baby_toys',
        }
        # Check by name matching if direct mapping is needed
        target_public_cat_ref = category_mapping.get(self.categ_id.name.upper()) or category_mapping.get(self.categ_id.name)
        if target_public_cat_ref:
            target_cat = self.env.ref(target_public_cat_ref, raise_if_not_found=False)
            if not target_cat:
                # Fallback to search by name if XML ID fails
                target_cat = self.env['product.public.category'].sudo().search([('name', '=ilike', self.categ_id.name)], limit=1)
            if target_cat and target_cat not in self.public_categ_ids:
                self.write({'public_categ_ids': [(4, target_cat.id)]})
