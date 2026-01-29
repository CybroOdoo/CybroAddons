# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, models


class SaleOrderLine(models.Model):
    """This class is to set the dealer price"""
    _inherit = "sale.order.line"

    @api.constrains('product_uom_qty', 'product_id', 'order_id.partner_id')
    def _check_dealer_price(self):
        """This function calculates price unit based on dealer price"""
        for line in self:
            if line.order_id.partner_id.dealer:
                if line.product_id.dealer_price and line.product_id.minimum_quantity:
                    if line.product_uom_qty >= line.product_id.minimum_quantity:
                        line.write(
                            {'price_unit': line.product_id.dealer_price})
                else:
                    line.write(
                        {'price_unit': line.product_id.lst_price})
            else:
                line.write(
                    {'price_unit': line.product_id.lst_price})
