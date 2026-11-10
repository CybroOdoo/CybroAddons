# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import models


class AccountMoveLine(models.Model):
    """Extend account.move.line to create stock moves from invoice lines."""
    _inherit = 'account.move.line'

    def _prepare_stock_move_vals(self, picking):
        """Prepare the values used to create the stock move of the line.

        :param picking: the picking the stock move belongs to
        :return: values for the creation of a ``stock.move``
        :rtype: dict
        """
        self.ensure_one()
        picking_type = picking.picking_type_id
        partner = self.move_id.partner_id
        if picking_type.code == 'outgoing':
            location = picking_type.default_location_src_id
            location_dest = (
                partner.property_stock_customer
                or self.env.ref('stock.stock_location_customers'))
        else:
            location = (
                partner.property_stock_supplier
                or self.env.ref('stock.stock_location_suppliers'))
            location_dest = picking_type.default_location_dest_id
        return {
            'description_picking': self.name or '',
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'location_id': location.id,
            'location_dest_id': location_dest.id,
            'picking_id': picking.id,
            'state': 'draft',
            'company_id': self.move_id.company_id.id,
            'price_unit': self.price_unit,
            'picking_type_id': picking_type.id,
            'warehouse_id': picking_type.warehouse_id.id,
        }

    def _create_stock_moves(self, picking):
        """Create the stock moves of the given picking from the lines.

        :param picking: the picking the stock moves belong to
        :return: the created stock moves
        :rtype: recordset of ``stock.move``
        """
        return self.env['stock.move'].create(
            [line._prepare_stock_move_vals(picking) for line in self])
