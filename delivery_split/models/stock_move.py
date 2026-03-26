# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class StockMove(models.Model):
    """Inheriting the stock move model"""
    _inherit = 'stock.move'
    _description = 'Stock Move Delivery Split'

    def _key_assign_picking(self):
        """ Computes and returns a key used for assigning a picking."""
        keys = super()._key_assign_picking()

        if self.sale_line_id and self.sale_line_id.order_id.is_delivery_split:
            order = self.sale_line_id.order_id

            keys += (order.id,)

            if not order.is_consolidate:
                keys += (self.id,)
            else:
                recipient = self.sale_line_id.recipient_id
                if recipient:
                    keys += (recipient.id,)

        return keys

    def _search_picking_for_assignation(self):
        """Searches for the relevant stock picking to assign based on the sale order
        and delivery split configuration."""
        self.ensure_one()

        if self.sale_line_id and self.sale_line_id.order_id.is_delivery_split:
            order = self.sale_line_id.order_id

            if not order.is_consolidate:
                return self.env['stock.picking']

            recipient = self.sale_line_id.recipient_id
            if recipient:
                return self.env['stock.picking'].search([
                    ('partner_id', '=', recipient.id),
                    ('sale_id', '=', order.id),
                    ('state', 'in', ['draft', 'confirmed', 'waiting', 'assigned'])
                ], limit=1)

        return super()._search_picking_for_assignation()
