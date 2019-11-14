# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan @cybrosys(odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields, api, _


class ProductPrice(models.TransientModel):
    _name = 'product.price'

    name = fields.Many2one('product.template', string="Product", required=True)
    sale_price = fields.Integer(string="Sale Price", required=True)
    cost_price = fields.Integer(string="Cost Price", required=True)

    def change_product_price(self):
        prod_obj = self.env['product.template'].search([('id', '=', self.name.id)])
        prod_value = {'list_price': self.sale_price, 'standard_price': self.cost_price}
        prod_obj.write(prod_value)
        return {
            'name': _('Products'),
            'view_mode': 'form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'res_id': prod_obj.id,
            'context': self.env.context
        }

    @api.onchange('name')
    def get_price(self):
        self.sale_price = self.name.list_price
        self.cost_price = self.name.standard_price


