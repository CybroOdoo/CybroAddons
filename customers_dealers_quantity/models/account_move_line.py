# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Athira Premanand (odoo@cybrosys.com)
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
    """This class is to set the dealer price"""
    _inherit = "account.move.line"

    @api.onchange('product_id', 'quantity')
    def _onchange_quantity(self):
        """This method is used for setting the dealer price"""
        if self.move_id.move_type == 'out_invoice':
            if self.move_id.partner_id.dealer:
                if self.product_id.price and self.product_id.minimum_quantity:
                    if self.quantity >= self.product_id.minimum_quantity:
                        self.price_unit = self.product_id.price
                    else:
                        self.price_unit = self.product_id.lst_price
            else:
                self.price_unit = self.product_id.lst_price
