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
from odoo import api, fields, models

class PosOrder(models.Model):
    """Extend POS order to link with hotel bookings."""
    _inherit = 'pos.order'

    booking_id = fields.Many2one('room.booking', string='Hotel Booking', help='Hotel booking associated with this POS order.')
    hotel_pos_status = fields.Selection([
        ('draft', 'New'),
        ('cancel', 'Cancelled'),
        ('paid', 'Paid'),
        ('done', 'Posted'),
        ('invoiced', 'Posted'),
    ], string='Status', compute='_compute_hotel_pos_status',
       help='Status of the POS order in relation to hotel room booking billing.')

    @api.depends('state', 'account_move.payment_state')
    def _compute_hotel_pos_status(self):
        """Compute hotel POS order status."""
        for order in self:
            if order.state == 'invoiced' and order.account_move:
                if order.account_move.payment_state == 'paid':
                    order.hotel_pos_status = 'paid'
                else:
                    order.hotel_pos_status = 'invoiced'
            else:
                order.hotel_pos_status = order.state


    def _ensure_hotel_pos_line(self):
        """Ensure the booking shows the POS order under the 'POS Orders' tab.

        The POS can create an order as draft first and later update/validate it (same uuid),
        adding the hotel-charge payment method afterwards. In that flow, relying only on
        `create()` is not enough.
        """
        HotelPosLine = self.env['hotel.pos.line']
        for order in self:
            if not order.booking_id:
                continue

            link = HotelPosLine.search([('pos_order_id', '=', order.id)], limit=1)
            if link:
                if link.booking_id != order.booking_id:
                    link.booking_id = order.booking_id.id
                continue

            HotelPosLine.create({
                'booking_id': order.booking_id.id,
                'pos_order_id': order.id,
            })

    @api.model
    def _order_fields(self, ui_order):
        """Add booking_id to the order fields"""
        res = super()._order_fields(ui_order)
        res['booking_id'] = ui_order.get('booking_id', False)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Create Hotel POS Line if the order is charged to a room"""
        orders = super().create(vals_list)
        orders._ensure_hotel_pos_line()
        return orders

    def write(self, vals):
        """Update POS order and ensure booking linkage."""
        res = super().write(vals)
        self._ensure_hotel_pos_line()
        return res

    @api.model
    def _process_order(self, order, draft, existing_order):
        """Ensure booking linkage survives the POS sync lifecycle.

        In Odoo 17, POS orders can be created/updated in multiple passes. We
        re-apply booking_id after super() and then ensure the hotel POS link.
        """
        booking_id = order.get('booking_id')
        order_id = super()._process_order(order, draft, existing_order)
        pos_order = self.browse(order_id)
        if booking_id and pos_order.booking_id.id != booking_id:
            pos_order.write({'booking_id': booking_id})
        pos_order._ensure_hotel_pos_line()
        return order_id

    def _process_saved_order(self, draft):
        """Force invoice creation for hotel 'Pay at Checkout' orders.

        When any payment line uses a hotel charge method, the order MUST go
        through invoicing so the invoice stays 'Not Paid' (deferred to checkout).
        This guarantees the flow:
          pos.order → invoiced state + unpaid account.move → smart button visible.
        """
        is_hotel_charge = any(
            p.payment_method_id.is_hotel_charge for p in self.payment_ids
        )
        if is_hotel_charge and not self.to_invoice:
            self.to_invoice = True
        return super()._process_saved_order(draft)

    def _apply_invoice_payments(self, is_reverse=False):
        """Override to keep the invoice unpaid for hotel 'Pay at Checkout' charges.

        In the hotel workflow the guest settles the bill at physical checkout, not
        at the POS terminal. Creating payment moves (even without explicit reconcile)
        can auto-settle the invoice receivable via journal configuration. We return
        an empty recordset so the invoice stays in 'Not Paid' state until checkout.

        For mixed orders (hotel charge + another method) the hotel charge method
        defers settlement, so we skip all payment move creation for simplicity.
        """
        is_hotel_charge = any(p.payment_method_id.is_hotel_charge for p in self.payment_ids)
        if is_hotel_charge:
            # Return empty moves — invoice stays open for checkout settlement
            return self.env['account.move']

        return super()._apply_invoice_payments(is_reverse=is_reverse)

class AccountMove(models.Model):
    """Customize payment status for hotel POS invoices."""
    _inherit = 'account.move'

    @api.depends('payment_state', 'state', 'is_move_sent', 'pos_order_ids')
    def _compute_status_in_payment(self):
        """Override to show 'Not Paid' for hotel POS invoices even if they are sent.
        
        This aligns with the hotel workflow where POS charges are only settled at checkout.
        """
        super()._compute_status_in_payment()
        for move in self:
            if move.state == 'posted' and move.payment_state == 'not_paid':
                if move.pos_order_ids.filtered(lambda o: any(p.payment_method_id.is_hotel_charge for p in o.payment_ids)):
                    move.status_in_payment = 'not_paid'
