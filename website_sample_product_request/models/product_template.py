# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright(C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """This class represents the product template"""
    _inherit = "product.template"

    is_sample_product = fields.Boolean(string="Sample Product")

    @api.onchange('is_sample_product')
    def _onchange_is_sample_product(self):
        """This method set the sample product's price as 0"""
        if self.is_sample_product:
            self.list_price = 0.0

    def _get_combination_info(self, combination=False, product_id=False, add_qty=1.0,
                              uom_id=False, only_template=False):
        """This method returns the price of the sample product as zero while adding to cart."""
        res = super()._get_combination_info(combination=combination,
                                            product_id=product_id, add_qty=add_qty,
                                            uom_id=uom_id, only_template=only_template)
        if self.is_sample_product:
            res.update({
                'price': 0.0,
                'list_price': 0.0,
                'price_reduce': 0.0,
                'has_discounted_price': False,
            })
        return res
