# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)

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
##############################################################################
from odoo import models


class StockRule(models.Model):
    """ Inherits the stock.rule to update each move with the partner from
        corresponding sale order line. """
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom,
                               location_id, name, origin, company_id, values):
        """
        Extending the _get_stock_move_values function for updating the
        partner as the partner from the selected delivery address if it exists
        or the partner from the order. Returns a dictionary of values that will
        be used to create a stock move from a procurement.
        :param procurement: browse record
        :rtype: dictionary
        """
        res = super()._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin,
            company_id, values)
        if res.get('warehouse_id'):
            warehouse = self.env['stock.warehouse'].browse(res.get(
                'warehouse_id'))
            if res.get('order_id') and warehouse.delivery_steps in [
                'pick_ship', 'ship_only']:
                for data in res.get('order_id'):
                    for move in self.env['stock.move'].browse(data[-1]):
                        partner_id = move.sale_line_id.delivery_addr.id or \
                                     move.sale_line_id.order_id.partner_id.id
                        res.update({
                            'partner_id': partner_id
                        })
        return res
