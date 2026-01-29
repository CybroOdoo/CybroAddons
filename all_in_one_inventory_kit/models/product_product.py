# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
################################################################
from odoo import fields, models


class ProductProduct(models.Model):
    """ Inherits product.product """
    _inherit = 'product.product'

    product_stock_location_ids = fields.One2many('stock.quant',
                                                 'product_id',
                                                 help="Locations of the"
                                                      " products in stock")

    def get_wo_description(self):
        """Method for print pdf report """
        return self.env.ref(
            'all_in_one_inventory_kit.product_product_report_action')\
            .report_action(self, data='')
