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
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Inherits product.template."""
    _inherit = 'product.template'

    def default_pack_location(self):
        """Sets the default value for the 'location_id' field based
        on the current user's warehouse."""
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        if warehouse:
            return warehouse.lot_stock_id.id

    is_pack = fields.Boolean(string='Is a Pack', help="The product is a pack.")
    pack_price = fields.Integer(
        string="Pack Price", compute='_compute_pack_price', store=True,
        help="Total price of products inside the pack")
    pack_products_ids = fields.One2many(
        'pack.product', 'product_tmpl_id',
        string='Pack Products', copy=True, help="Products inside the pack")
    pack_quantity = fields.Integer(
        string='Pack Quantity', help="Pack quantity available")
    pack_location_id = fields.Many2one(
        'stock.location',
        domain=[('usage', 'in', ['internal', 'transit'])],
        default=default_pack_location, help="Warehouse", string="Warehouse")

    @api.depends('pack_products_ids', 'pack_products_ids.price')
    def _compute_pack_price(self):
        """It is to set total price of the pack according to the
        products in the pack."""
        price = 0
        for record in self:
            for line in record.pack_products_ids:
                price = price + line.price
            record.pack_price = price

    @api.model
    def create(self, values):
        """Here create function is over ride to check whether the product is
        a pack or not."""
        if values.get('is_pack', False):
            if not values.get('pack_products_ids', []):
                raise UserError(_(
                    'You need to add atleast one product in the Pack...!'))
            if values.get('type', False) == 'service':
                raise UserError(_(
                    'You cannot define a pack product as a service..!'))
        return super(ProductTemplate, self).create(values)

    def write(self, values):
        """Here, the write function is overridden to determine if
        there is at least one product inside the package."""
        super(ProductTemplate, self).write(values)
        if self.is_pack:
            if not self.pack_products_ids:
                raise UserError(_(
                    'You need to add atleast one product in the Pack...!'))
            if self.type == 'service':
                raise UserError(
                    _('You cannot define a pack product as a service..!'))

    def action_update_price_product(self):
        """Updates the 'list_price' field of the current object
         based on the value of the 'pack_price' field on button click."""
        self.list_price = self.pack_price

    def action_get_quantity(self):
        """It is to return the pack quantity."""
        total_quantity = 1
        flag = 1
        while flag:
            for line in self.pack_products_ids:
                if line.qty_available >= line.quantity * total_quantity:
                    continue
                else:
                    if line.product_id.type != 'product':
                        continue
                    flag = 0
                    break
            if flag:
                total_quantity = total_quantity + 1
        self.pack_quantity = total_quantity - 1

    def action_update_quantity(self):
        """It is to return the  updated pack quantity."""
        product_id = len(
            self.product_variant_ids) == 1 and self.product_variant_id.id
        location_id = self.pack_location_id.id
        if not location_id:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.company.id)], limit=1)
            location_id = warehouse.lot_stock_id.id
            if not location_id:
                raise UserError(_(
                    'You need to select the location to update'
                    ' the pack quantity...!'))
        self.env['stock.quant'].with_context(inventory_mode=True).sudo(
        ).create({
            'product_id': product_id,
            'location_id': location_id,
            'inventory_quantity': self.pack_quantity,
        })

    @api.onchange('pack_location_id')
    def _onchange_pack_location_id(self):
        """It is to change the available quantity based on location."""
        for line in self.pack_products_ids:
            stock_quant = self.env['stock.quant'].search(
                [('product_id', '=', line.product_id.id),
                 ('location_id', '=', self.pack_location_id.id)])
            if stock_quant:
                line.total_available_quantity = stock_quant.quantity
            else:
                line.total_available_quantity = stock_quant.quantity
