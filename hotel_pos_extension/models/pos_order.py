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
    ], string='Status', compute='_compute_hotel_pos_status')

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
    def _process_order(self, order, existing_order):
        """Ensure booking linkage survives the POS sync lifecycle.

        In Odoo 19, POS orders can be created/updated in multiple passes. We
        re-apply booking_id after super() and then ensure the hotel POS link.
        """
        booking_id = order.get('booking_id')
        order_id = super()._process_order(order, existing_order)
        pos_order = self.browse(order_id)
        if booking_id and pos_order.booking_id.id != booking_id:
            pos_order.write({'booking_id': booking_id})
        pos_order._ensure_hotel_pos_line()
        return order_id

    def _generate_pos_order_invoice(self):
        """Override to forcefully keep the invoice 'Not Paid' for hotel charges.
        We use a context flag that is caught by our AccountMoveLine.reconcile override.
        """
        is_hotel_charge = any(p.payment_method_id.is_hotel_charge for p in self.payment_ids)
        if is_hotel_charge:
            move = super(PosOrder, self.with_context(skip_pos_invoice_reconciliation=True))._generate_pos_order_invoice()

            move.line_ids.sudo().remove_move_reconcile()

            for payment in self.payment_ids:
                if payment.account_move_id:
                    payment.account_move_id.line_ids.sudo().remove_move_reconcile()

            self.env['account.partial.reconcile'].sudo().search([
                '|', ('debit_move_id', 'in', move.line_ids.ids),
                ('credit_move_id', 'in', move.line_ids.ids)
            ]).unlink()

            move.sudo()._compute_amount()
            move._compute_payment_state()
            return move
            
        return super()._generate_pos_order_invoice()

    def _reconcile_invoice_payments(self, invoice, payment_moves):
        """Secondary layer to skip reconciliation for hotel room charges in Odoo 19."""
        is_hotel_charge = any(p.payment_method_id.is_hotel_charge for p in self.payment_ids)
        if self.env.context.get('skip_pos_invoice_reconciliation') or is_hotel_charge:
            return

        return super()._reconcile_invoice_payments(invoice, payment_moves)

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
