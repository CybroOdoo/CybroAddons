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


class ProductInventoryLocation(models.TransientModel):
    """
        Model for changing product inventory location
    """
    _name = 'product.inventory.location'
    _description = 'Product Inventory Location'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   readonly=True,
                                   help='Products which are selected to '
                                        'update the Inventory location')
    inventory_location_id = fields.Many2one('stock.location',
                                            string='Inventory Location',
                                            required=True,
                                            help='New Inventory location of '
                                                 'the products to update',
                                            domain="[('usage','=','inventory')]")

    def action_change_inventory_location(self):
        """
        Function for changing product inventory location of selected products
        """
        for products in self.product_ids:
            products.write(
                {'property_stock_inventory': self.inventory_location_id})
