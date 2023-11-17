"""Alternative product selection in pos"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class PosStock(models.Model):
    """This class is used to compute the quantity and returns the product"""
    _inherit = 'stock.quant'

    def pos_stock_product(self, id):
        """It is used to check the available quantity of the selected product"""
        val = self.env['product.product'].browse(id)
        if val.qty_available <= 0:
            return 0
        else:
            return val

    def pos_alternative_product(self, alter_id, code):
        """It is used to take the corresponding product in the
        product.product"""
        pos_product = 0
        if code:
            product_id = self.env['product.product'].search(
                [('product_tmpl_id', '=', alter_id),
                 ('default_code', '=', code)], limit=1)
            if product_id:
                pos_product = self.product_in_pos(product_id.id)

            return pos_product
        else:
            product_id = self.env['product.product'].search(
                [('product_tmpl_id', '=', alter_id)], limit=1)
            if product_id:
                pos_product = self.product_in_pos(product_id.id)
            return pos_product

    def product_in_pos(self, id):
        """This is used to check tha product is available in pos"""
        available_pos = self.env['product.product'].browse(
            id).available_in_pos
        if available_pos:
            return id
        else:
            return 0
