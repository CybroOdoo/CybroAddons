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


class ProductAccessory(models.TransientModel):
    """
    Model for adding Accessory Products
    """
    _name = 'product.accessory'
    _description = 'Product Accessory'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    accessory_ids = fields.Many2many('product.product',
                                     string="Accessory Products",
                                     help='Products wanted to added as Accessory Products')

    def action_add_accessory_products(self):
        """
        Function for adding Accessory Products for the selected products
        """
        if self.product_ids and self.accessory_ids:
            for products in self.product_ids:
                for items in self.accessory_ids:
                    products.accessory_product_ids = [
                        fields.Command.link(items.id)]
