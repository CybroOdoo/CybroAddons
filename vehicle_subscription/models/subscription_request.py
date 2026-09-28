# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhijith CK(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class SubscriptionRequest(models.Model):
    """New model subscription.request"""
    _name = "subscription.request"
    _description = "Subscription Request"
    _inherit = "mail.thread"
    _rec_name = "new_vehicle_id"

    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Choose the customer for subscription "
                                       "request")
    sale_id = fields.Many2one('sale.order', string='sale', readonly=True,
                              help="Helps you to store sale order")
    refund_id = fields.Many2one('account.move', string='Refund', readonly=True)
    current_vehicle_id = fields.Many2one('fleet.vehicle',
                                         string="Current Vehicle",
                                         help="Currently using vehicle of "
                                              "customer will be set",
                                         required=True)
    new_vehicle_id = fields.Many2one('fleet.vehicle', string="New Vehicle"
                                     , domain="[('id', 'in', vehicle_ids)]",
                                     help="Can choose different vehicle "
                                          "with same model", required=True)
    vehicle_ids = fields.Many2many('fleet.vehicle',
                                   compute='_compute_vehicle_ids',
                                   help="Compute and can choose vehicle with "
                                        "satisfying domain ")
    reason_to_change = fields.Char(string="Reason", required=True,
                                   help="Reason for changing vehicle")
    state = fields.Selection(
        selection=[('to_approve', 'To Approve'),
                   ('approved', 'Approved'),
                   ], string='State', default='to_approve',
        help="States of subscription")
    is_subscription = fields.Boolean(string="Subscription",
                                     help="Online Subscriptions")

    @api.depends('current_vehicle_id')
    def _compute_vehicle_ids(self):
        """This method searches for vehicles excluding the current vehicle,
        updating available vehicles for request approval."""
        for record in self:
            if record.current_vehicle_id and record.current_vehicle_id.exists():
                record.vehicle_ids = self.env['fleet.vehicle'].sudo().search([
                    ('id', '!=', record.current_vehicle_id.id)
                ])
            else:
                record.vehicle_ids = False

    def action_approve(self):
        """ Process the approval of the subscription request and update all vehicle-related fields.
        Preserves posted financial records and generates supplementary invoice or credit note
        if the subscription price changes upon vehicle swap."""
        subscription = self.env['fleet.subscription'].sudo().search(
            [('vehicle_id', '=', self.current_vehicle_id.id),
             ('state', '=', 'subscribed')], limit=1)
        if not subscription:
            subscription = self.env['fleet.subscription'].sudo().search(
                [('customer_id', '=', self.customer_id.id),
                 ('state', '=', 'subscribed')], limit=1)
        if not subscription:
            return

        old_vehicle_name = subscription.vehicle_id.name

        # Calculate invoiced/paid amount before updating
        all_invoices = subscription.invoice_ids | subscription.sale_id.invoice_ids
        posted_invoices = all_invoices.filtered(lambda inv: inv.state == 'posted')
        total_paid_or_invoiced = sum(posted_invoices.mapped('amount_untaxed_signed'))

        # Lookup new vehicle's insurance record
        new_insurance = self.env['vehicle.insurance'].sudo().search(
            [('vehicle_id', '=', self.new_vehicle_id.id)], limit=1)

        write_vals = {
            'vehicle_id': self.new_vehicle_id.id,
            'insurance_type_id': new_insurance.id if new_insurance else False,
            'invisible_sub': True,
        }
        if self.new_vehicle_id.model_id and self.new_vehicle_id.model_id.seats:
            write_vals['seating_capacity'] = self.new_vehicle_id.model_id.seats
        if self.new_vehicle_id.fuel_rate:
            write_vals['fuel_rate'] = self.new_vehicle_id.fuel_rate
        if self.new_vehicle_id.charge_km:
            write_vals['charge_km'] = self.new_vehicle_id.charge_km

        subscription.write(write_vals)
        self.write({'state': 'approved'})

        # Log change event in chatter
        subscription.message_post(
            body=f"Vehicle subscription changed from <b>{old_vehicle_name}</b> to <b>{self.new_vehicle_id.name}</b>."
        )

        # Update Sales Order line description safely
        sale_order = subscription.sale_id
        if sale_order and sale_order.order_line:
            sale_order.order_line[0].write({
                'name': self.new_vehicle_id.name,
                'price_unit': subscription.price + subscription.extra_price,
            })

        # Update ONLY draft invoices. Posted/Paid invoices remain immutable!
        draft_invoices = subscription.invoice_ids.filtered(lambda inv: inv.state == 'draft')
        for rec in draft_invoices:
            if rec.invoice_line_ids:
                rec.invoice_line_ids[0].write({
                    'name': self.new_vehicle_id.name,
                    'price_unit': subscription.price + subscription.extra_price,
                })

        # Handle price differential for posted/paid subscriptions
        if posted_invoices:
            new_total = round(subscription.price + subscription.extra_price, 2)
            price_diff = round(new_total - total_paid_or_invoiced, 2)
            product_template_id = self.env.ref('vehicle_subscription.product_template_vehicle_subscription_form').id
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id)], limit=1)
            so_line_command = [fields.Command.link(sale_order.order_line[0].id)] if sale_order and sale_order.order_line else []

            if price_diff > 0:
                # Vehicle Upgrade: Generate Supplementary Draft Invoice for the price difference
                inv = self.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': subscription.customer_id.id,
                    'is_subscription': True,
                    'invoice_origin': sale_order.name if sale_order else False,
                    'invoice_line_ids': [fields.Command.create({
                        'product_id': product_id.id,
                        'name': f"Subscription Vehicle Upgrade Adjustment: {old_vehicle_name} -> {self.new_vehicle_id.name}",
                        'price_unit': price_diff,
                        'sale_line_ids': so_line_command,
                    })]
                })
                subscription.invoice_ids = [fields.Command.link(inv.id)]
                if sale_order:
                    inv.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': inv, 'origin': sale_order},
                        subtype_xmlid='mail.mt_note',
                    )
            elif price_diff < 0:
                # Vehicle Downgrade: Generate Draft Credit Note for the refund difference
                refund_amount = abs(price_diff)
                refund_inv = self.env['account.move'].create({
                    'move_type': 'out_refund',
                    'partner_id': subscription.customer_id.id,
                    'is_subscription': True,
                    'invoice_origin': sale_order.name if sale_order else False,
                    'invoice_line_ids': [fields.Command.create({
                        'product_id': product_id.id,
                        'name': f"Subscription Vehicle Downgrade Credit: {old_vehicle_name} -> {self.new_vehicle_id.name}",
                        'price_unit': refund_amount,
                        'sale_line_ids': so_line_command,
                    })]
                })
                subscription.refund_id = refund_inv
                subscription.invoice_ids = [fields.Command.link(refund_inv.id)]
                if sale_order:
                    refund_inv.message_post_with_source(
                        'mail.message_origin_link',
                        render_values={'self': refund_inv, 'origin': sale_order},
                        subtype_xmlid='mail.mt_note',
                    )
