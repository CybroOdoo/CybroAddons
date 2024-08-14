# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
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
from odoo import api, models


class StockLot(models.Model):
    """Serial Number Validation Model.This model is used for serial number
       validation in Odoo."""
    _inherit = 'stock.lot'

    @api.model
    def validate_lots(self, lots):
        """ This method validates a list of lots."""
        processed = []
        LotObj = self.env['stock.lot']
        for lot in lots:
            lot_id = LotObj.search([('name', '=', lot)], limit=1)
            if lot in processed:
                return ['duplicate', lot]
            if lot_id.product_qty <= 0:
                return ['no_stock', lot]
            processed.append(lot)
        return True

    @api.model
    def get_available_lots_qty_pos(self, product_id, lot_name):
        """Check the max lot quantity of corresponding product."""
        stock_quant = self.env['stock.lot'].search([
            ('product_id', '=', product_id), ('name', '=', lot_name)])
        return stock_quant.product_qty
