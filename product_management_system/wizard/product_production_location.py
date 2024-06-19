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


class ProductProductionLocation(models.TransientModel):
    """
        Model for changing production location
    """
    _name = 'product.production.location'
    _description = 'Product Production Location'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   help='Products which are selected')
    production_location_id = fields.Many2one('stock.location',
                                             string='Production Location',
                                             help='Production location of the products',
                                             domain="[('usage','=','production')]")

    def action_change_production_location(self):
        """
        Function for changing production location of the selected products
        """
        if self.product_ids:
            for products in self.product_ids:
                products.write(
                    {'property_stock_production': self.production_location_id})
