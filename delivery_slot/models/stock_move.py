# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class StockMove(models.Model):
    """Create one picking per move for orders with delivery slot per product"""
    _inherit = 'stock.move'

    def _is_slot_per_product(self):
        """Check if the move belongs to an order using delivery slots."""
        self.ensure_one()
        return self.sale_line_id.order_id.slot_per_product

    def _key_assign_picking(self):
        """Give every slot move its own grouping key."""
        key = super()._key_assign_picking()
        if self._is_slot_per_product():
            return tuple(key) + (self.id,)
        return key

    def _search_picking_for_assignation(self):
        """Never reuse an existing picking for slot moves."""
        if self._is_slot_per_product():
            return self.env['stock.picking']
        return super()._search_picking_for_assignation()
