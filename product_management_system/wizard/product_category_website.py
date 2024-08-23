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


class ProductWebsiteCategory(models.TransientModel):
    """
        Model for changing public_categ_ids (Website Category)
    """
    _name = 'product.category.website'
    _description = 'Product Website Category'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   readonly=True,
                                   help='Products which are selected to '
                                        'change the website category')
    public_categ_ids = fields.Many2many('product.public.category',
                                        string="Website Product Category",

                                        help='Select the new Website Category '
                                             'for selected Products')

    def action_change_website_category(self):
        """
        Function for changing public_categ_ids (Website Category) of Selected Products
        """
        for products in self.product_ids:
                products.public_categ_ids = [fields.Command.set(self.public_categ_ids.ids)]
