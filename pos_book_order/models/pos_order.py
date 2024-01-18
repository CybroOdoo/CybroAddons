# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class PosOrder(models.Model):
    """Inherited model for pos order,all confirmed booking orders are converted
       as pos orders"""
    _inherit = 'pos.order'

    booking_ref_id = fields.Many2one(
        'book.order', string='Booking Ref',
        help="Booked order reference for the pos order")

    @api.model
    def _order_fields(self, ui_order):
        """Overriding to pass value of booked order ref to PoS order
           ui_order(dict): dictionary of pos order field values
           dict: returns dictionary of pos order field values
        """
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        if ui_order.get('is_booked'):
            order_fields['booking_ref_id'] = ui_order.get('booked_data')['id']
            self.env['book.order'].browse(
                ui_order.get('booked_data')['id']).write(
                {'state': 'confirmed'})
        return order_fields