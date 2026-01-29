# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (<https://www.cybrosys.com>)
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
from odoo import fields, models


class SubscriptionRequest(models.Model):
    """New model subscription.request"""
    _name = "subscription.request"
    _description = "Subscription Request"
    _inherit = "mail.thread"
    _rec_name = "new_vehicle_id"

    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Choose the customer for subscription "
                                       "request", required=True, readonly=True)
    sale_id = fields.Many2one('sale.order', string='sale', readonly=True,
                              help="Helps you to store sale order")
    refund_id = fields.Many2one('account.move', string='Refund', readonly=True)
    current_vehicle_id = fields.Many2one('fleet.vehicle',
                                         string="Current Vehicle",
                                         required=True, readonly=True,
                                         help="Currently using vehicle of "
                                              "customer will be set")
    new_vehicle_id = fields.Many2one('fleet.vehicle',
                                     string="New Vehicle",
                                     readonly=True,
                                     required=True,
                                     help="Can choose different vehicle "
                                          "with same model")
    reason_to_change = fields.Char(string="Reason", required=True,
                                   readonly=True,
                                   help="Reason for changing vehicle")
    subscription_id = fields.Many2one('fleet.subscription',
                                      string='Subscription Id',
                                      help='Subscription related to this '
                                           'cancellation request')
    state = fields.Selection(
        selection=[('to_approve', 'To Approve'),
                   ('approved', 'Approved'),
                   ], string='State', default='to_approve',
        help="States of subscription")

    def action_approve(self):
        """ Process the approval of the subscription request."""
        subscription = self.env['fleet.subscription'].search(
            [('vehicle_id', '=', self.current_vehicle_id.id),
             ('state', '=', 'subscribed')])
        subscription.update({
            'vehicle_id': self.new_vehicle_id,
            'is_invisible_sub': True,
        })
        self.write({'state': 'approved'})
        sale_order = subscription.sale_id
        if sale_order.order_line:
            sale_order.order_line[0].name = self.new_vehicle_id.name
        invoice_ids = subscription.invoice_ids
        for rec in invoice_ids:
            if rec.invoice_line_ids:
                rec.invoice_line_ids[0].name = self.new_vehicle_id.name
        subscription.write({'sale_id': sale_order.id})
        subscription.write({'invoice_ids': invoice_ids.ids})
