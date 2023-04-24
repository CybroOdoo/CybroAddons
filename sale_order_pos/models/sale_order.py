# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class SaleOrder(models.Model):
    """Inheriting sale order for creating a sale order through POS"""
    _inherit = 'sale.order'

    def create_sale_order(self, temp_list, cus):
        """To create sale order through POS"""
        self.create({
                'partner_id': cus.get('id'),
                'order_line': [(0, 0, {
                    'product_id': rec.get('product'),
                    'discount': rec.get('discount'),
                    'product_uom_qty': rec.get('quantity'),
                    'price_subtotal': rec.get('price'),
                }) for rec in temp_list]
            })
