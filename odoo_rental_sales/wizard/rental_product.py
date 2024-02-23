# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswathi PN (odoo@cybrosys.com)
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


class RentalProduct(models.TransientModel):
    """Creating a wizard that showing the rental product details"""

    _name = 'rental.product'
    _description = 'Rental Product'

    rental_product_id = fields.Many2one('product.product',
                                        domain=[('rental', '=', True)],
                                        string='Rental Product',
                                        help='To choose a rental product')
    unit_price = fields.Float(string='Unit Price',
                              related='rental_product_id.lst_price',
                              help='Field for adding the unit price of the '
                                   'product')
    qty = fields.Float(string='Quantity',
                       help="Adding the required quantity of the product",
                       default=1)

    def add_rental_product(self):
        """Function for adding the rental product to the sale order line"""
        sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
        self.env['sale.order.line'].create({
            'product_id': self.rental_product_id.id,
            'order_id': sale.id,
            'product_uom_qty': self.qty, })
