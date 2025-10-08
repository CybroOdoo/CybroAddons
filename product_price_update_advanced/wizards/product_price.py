# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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


class ProductPrice(models.TransientModel):
    """Wizard for updating the sale and cost price of the product"""
    _name = 'product.price'
    _description = 'Product Price'

    product_id = fields.Many2one('product.template', string="All Products",
                                 required=True,
                                 help="select the product for changing"
                                      "the sales and cost price")
    sale_price = fields.Integer(string="Sale Price", required=True,
                                help="The required price for updating the sale"
                                     "price")
    cost_price = fields.Integer(string="Cost Price", required=True,
                                help="The required price for updating the cost"
                                     "price")

    def action_change_product_price(self):
        """Open a wizard with current sale and cost price of selected product.
                :return: returns to the product form with updated price"""
        products = self.env['product.template'].browse(self.product_id.id)
        products.write({'list_price': self.sale_price,
                        'standard_price': self.cost_price})
        return {
            'name': _('Products'),
            'view_mode': 'form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'res_id': products.id,
            'context': self.env.context
        }

    @api.onchange('product_id')
    def _onchange_name(self):
        """Updates the selected product's sale and cost price"""
        self.sale_price = self.product_id.list_price
        self.cost_price = self.product_id.standard_price
