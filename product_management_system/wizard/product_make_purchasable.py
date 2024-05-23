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


class ProductMakePurchasable(models.TransientModel):
    """
        Model for making product purchasable
    """
    _name = 'product.make.purchasable'
    _description = 'Make Product Purchasable'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')

    def action_product_make_purchasable_confirm(self):
        """
        Function for making product purchasable
        """
        if self.product_ids:
            for rec in self.product_ids:
                rec.write({
                    'purchase_ok': True
                })

    def action_product_make_purchasable_false(self):
        """
        Function for making product not purchasable
        """
        if self.product_ids:
            for rec in self.product_ids:
                rec.write({
                    'purchase_ok': False
                })
