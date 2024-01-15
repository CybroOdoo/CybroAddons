# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class SaleRecurringLine(models.Model):
    """SaleRecurringLine class represents a recurring order line"""
    _name = 'sale.recurring.line'
    _description = 'Recurring Line'

    product_id = fields.Many2one('product.product', string='Product',
                                 required=True,
                                 help='Select a product for which the sale'
                                      ' recurring will be used')
    name = fields.Char(string='Description', related='product_id.name',
                       help='Name of the product')
    price_unit = fields.Float(string='Price',
                              related='product_id.list_price',
                              help='Product price')
    product_uom_qty = fields.Float(string='Quantity', default=1,
                                   help='Total number of quantity')
    order_id = fields.Many2one('sale.recurring', string="Order",
                               help='Order details')
