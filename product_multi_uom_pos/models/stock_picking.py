# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali VP (Contact : odoo@cybrosys.com)
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
from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _prepare_stock_move_vals(self, first_line, order_lines):
        """Prepare values for the stock.move record.

        When the cashier selected a custom UoM (e.g. Carton = 24 pcs) we want
        the stock move to reflect that UoM and the original POS qty, not the
        base-unit quantity.  All order lines in the group share the same product
        so they all have the same selected_uom_id (if any).
        """
        selected_uom = first_line.selected_uom_id
        product_default_uom = first_line.product_id.uom_id

        if selected_uom and selected_uom != product_default_uom:
            # Keep the UoM as chosen in POS – stock will convert internally
            uom_id = selected_uom.id
            # Sum the POS quantities; they are already in the selected UoM
            qty = abs(sum(order_lines.mapped('qty')))
        else:
            uom_id = product_default_uom.id
            qty = abs(sum(order_lines.mapped('qty')))

        vals = super()._prepare_stock_move_vals(first_line, order_lines)
        vals.update({
            'product_uom': uom_id,
            'product_uom_qty': qty,
        })
        return vals
