# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


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
                                              "customer will be set")
    new_vehicle_id = fields.Many2one('fleet.vehicle', string="New Vehicle"
                                     , domain="[('id', 'in', vehicle_ids)]",
                                     help="Can choose different vehicle "
                                          "with same model")
    vehicle_ids = fields.Many2many('fleet.vehicle',
                                   compute='_compute_vehicle_ids',
                                   help="Compute and can choose vehicle with "
                                        "satisfying domain ")
    reason_to_change = fields.Char(string="Reason",
                                   help="Reason for changing vehicle")
    state = fields.Selection(
        selection=[('to_approve', 'To Approve'),
                   ('approved', 'Approved'),
                   ], string='State', default='to_approve',
        help="States of subscription")

    @api.depends('current_vehicle_id')
    def _compute_vehicle_ids(self):
        """This method searches for vehicles with the same model and brand
        as the current vehicle, excluding the current vehicle itself.
        The vehicle IDs are updated accordingly, and the state
        is set to 'to_approve'."""
        self.vehicle_ids = False
        model_id = self.env['fleet.vehicle'].search(
            [('model_id', '=', self.current_vehicle_id.model_id.id),
             ('model_id.brand_id', '=',
              self.current_vehicle_id.model_id.brand_id.id),
             ('id', '!=', self.current_vehicle_id.id)])
        for record in model_id:
            self.vehicle_ids = [(4, record.id)]
        self.write({'state': 'to_approve'})

    def action_approve(self):
        """ Process the approval of the subscription request."""
        subscription = self.env['fleet.subscription'].search(
            [('vehicle_id', '=', self.current_vehicle_id.id),
             ('state', '=', 'subscribed')])
        subscription.update({
            'vehicle_id': self.new_vehicle_id,
            'invisible_sub': True,
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
