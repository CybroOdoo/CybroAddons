# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Jumana Jabin MP(<http://www.cybrosys.com>)
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
    """
    This class is inherited for adding a new function to validate the lots and
    serial numbers.
    Methods:
        validate_lots(lots):
            check and validate the lots and serial numbers for the product
            based on the stock location.
    """
    _inherit = 'stock.lot'

    @api.model
    def validate_lots(self, lots, product_id, picking_type_id):
        """ To check
        - the invalid lots/ serial numbers
        - duplicate serial numbers
        - insufficient stock for the lots or serial numbers.
        All these cases are checked based on the product and the stock location
        set for the active PoS.
        Args:
           lots (list[str,..., str]): the lots for validation.
           product_id (int): id of the selected product.
           picking_type_id (int): id of the operation type added for the PoS.
        Returns:
            list[str, str] or Bool: True if the lot is valid, else the list of
            the string that indicates the exception: 'invalid', 'duplicate' or
            'no_stock' with the lot/ serial number.
        """
        processed = []
        if not product_id:
            return ['invalid', 'product']
        for lot in lots:
            stock_lots = self.sudo().search([
                ('name', '=', lot), ('product_id', '=', product_id)])
            if not stock_lots:
                return ['invalid', lot]
            picking_type = self.env['stock.picking.type'].sudo().browse(
                picking_type_id)
            stock_quant = self.env['stock.quant'].sudo().search(
                [('location_id', '=', picking_type.default_location_src_id.id),
                 ('lot_id', 'in', stock_lots.ids)])
            if (stock_quant and stock_quant.available_quantity > 0
                    and lot not in processed):
                processed.append(lot)
            else:
                if lot in processed:
                    return ['duplicate', lot]
                return ['no_stock', lot]
        return True
