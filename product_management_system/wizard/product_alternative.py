# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class ProductAlternative(models.TransientModel):
    """
        Model for adding alternative products
    """
    _name = 'product.alternative'
    _description = 'Alternative Product'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    alternative_ids = fields.Many2many('product.template',
                                       'product_management_alternative_rel',
                                       string="Alternative Products",
                                       help='Alternative Products',
                                       domain="[('id', 'not in', product_ids)]")

    def action_add_alternative_products(self):
        """
        Function for adding alternative products for Selected Products
        """
        if self.product_ids and self.alternative_ids:
            for products in self.product_ids:
                for items in self.alternative_ids:
                    products.alternative_product_ids = [
                        fields.Command.link(items.id)]
