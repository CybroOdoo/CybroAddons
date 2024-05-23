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


class ProductUpdatePrice(models.TransientModel):
    """
        Model for updating price
    """
    _name = 'product.update.price'
    _description = 'Update Product Price'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    product_price = fields.Float(string='Price to change',
                                 help='Price of the product')

    def action_product_update_price_confirm(self):
        """
        Function for updating price of the selected products
        """
        if self.product_ids:
            for rec in self.product_ids:
                rec.write({
                    'list_price': self.product_price if self.product_price != 0 else rec.list_price,
                })
