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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
        
class RoomBooking(models.Model):
    """Extend room booking to include POS order tracking."""
    _inherit = 'room.booking'

    pos_order_line_ids = fields.One2many('hotel.pos.line', 'booking_id', string='POS Orders', help='List of POS order lines associated with this room booking.')
    amount_total_pos = fields.Monetary(string="Total POS Amount", compute='_compute_amount_total_pos', store=False, help='Total amount from all linked POS orders.')
    has_pos_orders = fields.Boolean(string="Has POS Orders", compute='_compute_has_pos_orders', store=False, help='Indicates whether this booking has linked POS orders.')

    @api.depends('pos_order_line_ids')
    def _compute_has_pos_orders(self):
        """Compute if booking has linked POS orders."""
        for rec in self:
            rec.has_pos_orders = bool(rec.pos_order_line_ids)

    @api.depends(
        'room_line_ids.price_subtotal', 'room_line_ids.price_tax', 'room_line_ids.price_total',
        'food_order_line_ids.price_subtotal', 'food_order_line_ids.price_tax', 'food_order_line_ids.price_total',
        'service_line_ids.price_subtotal', 'service_line_ids.price_tax', 'service_line_ids.price_total',
        'vehicle_line_ids.price_subtotal', 'vehicle_line_ids.price_tax', 'vehicle_line_ids.price_total',
        'event_line_ids.price_subtotal', 'event_line_ids.price_tax', 'event_line_ids.price_total',
        'pos_order_line_ids.pos_order_id.amount_total',
        'pos_order_line_ids.pos_order_id.currency_id',
        'pos_order_line_ids.pos_order_id.state',
    )
    def _calculate_amounts(self, flag=False):
        """Extended calculation to include POS charges and add to invoice list"""
        if hasattr(super(), '_calculate_amounts'):
            res = super()._calculate_amounts(flag=flag)
        else:
            res_list = []
            for rec in self:
                vals = {
                    'amount_untaxed': rec.amount_untaxed,
                    'amount_tax': rec.amount_tax,
                    'amount_total': rec.amount_total,
                }
                booking_list = []
                if flag:
                    # Parent returns a list of items for the record
                    booking_list = rec._compute_amount_untaxed(flag=True)
                res_list.append((vals, booking_list))
            res = res_list[0] if len(self) == 1 else res_list
        
        is_single = len(self) == 1
        res_list = [res] if is_single else res
        
        final_res = []
        for rec, (vals, booking_list) in zip(self, res_list):
            amount_total_pos = sum(rec.pos_order_line_ids.mapped('amount_total'))
            
            vals['amount_total_pos'] = amount_total_pos
            vals['amount_total'] += amount_total_pos
            vals['amount_untaxed'] += amount_total_pos 
            
            if flag:
                for line in rec.pos_order_line_ids:
                    for pos_line in line.pos_order_id.lines:
                        booking_list.append({
                            'name': f"POS: {pos_line.full_product_name or pos_line.product_id.name} (Ref: {line.pos_reference or ''})",
                            'quantity': pos_line.qty,
                            'price_unit': pos_line.price_unit,
                            'product_type': 'pos'
                        })
            final_res.append((vals, booking_list))
            
        return final_res[0] if is_single else final_res

    def _compute_amount_total_pos(self):
        """Compute POS amount total from calculated values."""
        for record in self:
            vals, _ = record._calculate_amounts()
            record.amount_total_pos = vals.get('amount_total_pos', 0.0)

    def get_bill_summary_lines(self):
        """Returns a list of summary lines for the bill report:
        [
          {'ref': '', 'order_no': 'S00048', 'date': '...', 'total': 123.45},
          {'ref': '', 'order_no': 'New/0011', 'date': '...', 'total': 456.78},
        ]
        Matches the 1st image layout.
        """
        self.ensure_one()
        lines = []

        folio_total = sum(self.room_line_ids.mapped('price_total')) + \
                      sum(self.food_order_line_ids.mapped('price_total')) + \
                      sum(self.service_line_ids.mapped('price_total')) + \
                      sum(self.vehicle_line_ids.mapped('price_total')) + \
                      sum(self.event_line_ids.mapped('price_total'))
                      
        lines.append({
            'reference': self.name,
            'order_no': self.name,
            'date': self.date_order,
            'total': folio_total,
        })
        
        for pos_link in self.pos_order_line_ids:
            lines.append({
                'reference': pos_link.pos_order_id.name,
                'order_no': pos_link.pos_order_id.pos_reference,
                'date': pos_link.pos_order_id.date_order,
                'total': pos_link.pos_order_id.amount_total,
            })
            
        return lines

    pos_invoice_count = fields.Integer(compute='_compute_pos_invoice_count', string='POS Invoice Count', help='Count of non-cancelled POS invoices linked to this room booking.')

    def _compute_pos_invoice_count(self):
        """Compute number of valid POS invoices linked to the record."""
        for rec in self:
            invoices = rec.pos_order_line_ids.mapped('pos_order_id.account_move')
            rec.pos_invoice_count = len(invoices.filtered(lambda x: x.state != 'cancel'))

    def action_view_pos_invoices(self):
        """Open POS invoices related to the record."""
        self.ensure_one()
        invoices = self.pos_order_line_ids.mapped('pos_order_id.account_move').filtered(lambda x: x.state != 'cancel')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_done(self):
        """Override to block checkout if any POS hotel charge invoice is unpaid.

        In addition to the base check for the room invoice, we also validate
        that all 'Pay at Checkout' POS invoices have been settled before the
        booking can move to Done state.
        """
        # Check POS hotel charge invoices
        pos_invoices = self.pos_order_line_ids.mapped('pos_order_id').filtered(
            lambda o: any(p.payment_method_id.is_hotel_charge for p in o.payment_ids)
        ).mapped('account_move').filtered(lambda m: m.id and m.state != 'cancel')

        for invoice in pos_invoices:
            if invoice.payment_state in ('not_paid', 'partial'):
                raise ValidationError(
                    _('Your Invoice (%s) is Due for Payment.') % invoice.name
                )

        return super().action_done()

    def action_compute_bill(self):
        """Open the Compute Bill wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Compute Bill',
            'res_model': 'compute.bill',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_booking_id': self.id}
        }

