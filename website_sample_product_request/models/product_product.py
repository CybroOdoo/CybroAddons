# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhil (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api,models



class ProductProduct(models.Model):
    """ When a product is marked as a sample, its list price is set to 0.0."""
    _inherit = "product.product"


    @api.onchange('is_sample_product')
    def _onchange_is_sample_product(self):
        """Change the product price when it is sample product"""
        self.lst_price = 0.0 if self.is_sample_product else self.lst_price

    @api.model
    def create(self, vals):
        """Override the create method to ensure that when a product is created
        through the 'Sample Variant' action, the 'is_sample_product' field
        is automatically set to True.
        """
        if self._context.get('default_is_sample_product'):
            vals['lst_price'] = 0.0
            vals['is_sample_product'] = True
        return super().create(vals)
