# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from datetime import date
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    """Inheriting stock move."""
    _inherit = 'stock.move'

    delivery_datetime = fields.Datetime(string='Delivery Date',
                                        help='Delivery date for the product')

    def _get_new_picking_values(self):
        """ added the custom field in this function which is return create
        values for new picking that will be linked with group of moves in self.
        """
        res = super(StockMove, self)._get_new_picking_values()
        if res.get('picking_type_id'):
            picking_type = self.env['stock.picking.type'].browse(
                res.get('picking_type_id'))
            if picking_type.code == 'outgoing':
                res['scheduled_date'] = self.delivery_datetime
        res['delivery_datetime'] = self.delivery_datetime
        return res

    def _search_picking(self, move):
        """To add delivery date to the corresponding move."""
        domain = [
            ('group_id', '=', move.group_id.id),
            ('location_id', '=', move.location_id.id),
            ('location_dest_id', '=', move.location_dest_id.id),
            ('picking_type_id', '=', move.picking_type_id.id),
            ('printed', '=', False),
            ('state', 'in', ['draft', 'confirmed', 'waiting',
                             'partially_available', 'assigned'])]
        if move.delivery_datetime:
            domain += [('delivery_datetime', '=', move.delivery_datetime)]
        return self.env['stock.picking'].search(domain, limit=1)

    @api.constrains('delivery_datetime')
    def _date_validation(self):
        """created for date validation, the delivery date should be after the
        today date."""
        for move in self:
            if move.delivery_datetime and move.delivery_datetime.date() < date.today():
                raise ValidationError("Date should be after the today date")

    def _assign_picking(self):
        """ Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). Otherwise, create a
        new picking to assign them to.
        """
        for move in self:
            recompute = False
            picking = self._search_picking(move)
            if picking:
                if picking.partner_id.id != move.partner_id.id or \
                        picking.origin != move.origin:
                    picking.write({
                        'partner_id': False,
                        'origin': False,
                    })
            else:
                recompute = True
                picking = picking.create(move._get_new_picking_values())
            move.write({'picking_id': picking.id})
            move._assign_picking_post_process(new=recompute)
        return True
