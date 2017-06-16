# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class ProductPrice(models.AbstractModel):
    _name = 'product.price'

    name = fields.Many2one('product.template', string="Product", required=True)
    sale_price = fields.Integer(string="Sale Price", required=True)
    cost_price = fields.Integer(string="Cost Price", required=True)

    @api.multi
    def change_product_price(self):
        prod_obj = self.env['product.template'].search([('name', '=', self.name.name)])
        prod_value = {'list_price': self.sale_price, 'standard_price': self.cost_price}
        obj = prod_obj.write(prod_value)
        return obj

    @api.onchange('name')
    def get_price(self):
        prod_obj = self.env['product.template'].search([('name', '=', self.name.name)])
        self.sale_price = prod_obj.list_price
        self.cost_price = prod_obj.standard_price





