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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PackProduct(models.Model):
    """ A new model is created to store products as pack."""

    _name = 'pack.product'
    _rec_name = 'product_tmpl_id'
    _description = 'Select Pack Products'

    product_id = fields.Many2one(
        'product.product', string='Product', required=True,
        domain=[('is_pack', '=', False)], help="Product")
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product', help="Product")
    price = fields.Float(
        string='Price', compute='_compute_price', store=True,
        help="Computed price of product according to the quantity.")
    quantity = fields.Integer(
        string='Quantity', default=1,
        help="Quantity of product that should be in the pack.")
    qty_available = fields.Float(
        string='Quantity Available', compute='_compute_qty_available',
        store=True, readonly=False, help="Available quantity of product.")
    total_available_quantity = fields.Float(
        string='Total Quantity',
        help="Total Quantity available of that product")

    @api.depends('product_id',
                 'total_available_quantity',
                 'product_id.qty_available')
    def _compute_qty_available(self):
        """It is to compute the available quantity."""
        for record in self:
            location_id = record.product_tmpl_id.pack_location_id
            if location_id:
                stock_quant = self.env['stock.quant'].search(
                    [('product_id', '=', record.product_id.id),
                     ('location_id', '=', location_id.id)])
                if stock_quant:
                    record.qty_available = stock_quant.quantity
                else:
                    record.qty_available = False
            else:
                record.qty_available = False

    @api.depends('product_id', 'quantity')
    def _compute_price(self):
        """It is to compute price of each product compared to quantity."""
        for record in self:
            record.price = record.product_id.lst_price * record.quantity

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """It is to set price."""
        self.price = self.product_id.lst_price * self.quantity

    @api.constrains('quantity')
    def _check_quantity(self):
        """This function is to ensure product quantity is positive."""
        if any([product.quantity < 0 for product in self]):
            raise ValidationError(_('You can not enter negative quantities.'))
