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


class AccountMoveLine(models.Model):
    """This inherit Account move line"""
    _inherit = "account.move.line"

    @api.onchange('product_id', 'quantity', 'move_id.partner_id')
    def _onchange_quantity(self):
        """This method is used for setting the dealers price"""
        for line in self:
            if line.move_id.move_type == 'out_invoice' and line.move_id.partner_id.dealer:
                if line.product_id.dealer_price and line.product_id.minimum_quantity:
                    if line.quantity >= line.product_id.minimum_quantity:
                        line.price_unit = line.product_id.dealer_price
                    else:
                        line.price_unit = line.product_id.lst_price
                else:
                    line.price_unit = line.product_id.lst_price
            else:
                line.price_unit = line.product_id.lst_price

            res = self._get_price_total_and_subtotal_model(
                line.price_unit, line.quantity, line.discount,
                line.move_id.currency_id, line.product_id,
                line.move_id.partner_id, line.tax_ids,
                line.move_id.move_type
            )
            line.price_subtotal = res['price_subtotal']
            line.price_total = res['price_total']
