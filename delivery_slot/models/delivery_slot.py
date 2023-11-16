# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Muhsina V (odoo@cybrosys.com)
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


class DeliverySlot(models.Model):
    """ Delivery slot model"""
    _name = 'delivery.slot'
    _description = 'Delivery slot'
    _rec_name = 'delivery_date'

    delivery_date = fields.Date(
        string='Delivery Date', default=fields.Date.today(),
        help="Choose a delivery date")
    slot_id = fields.Many2one('slot.time', string="slot",
                              help="Choose Delivery slot")
    delivery_ids = fields.One2many(
        'sale.order', 'delivery_slot_id', string="Delivery",
        compute="_compute_sale_ids", help="Related Deliveries")
    delivery_limit = fields.Integer(string="Delivery Limit", default=100,
                                    help="Limit of this delivery slot")
    total_delivery = fields.Integer(
        string="Total No of Deliveries", compute='_compute_total_delivery',
        help="Current deliveries in this slot")
    remaining_slots = fields.Integer(
        string="Available No of Deliveries", compute='_compute_remaining_slots'
        , help="Remaining no of deliveries in this slot")
    active = fields.Boolean(
        string='Active', default=True, help="Active or not")

    @api.depends('delivery_ids')
    def _compute_total_delivery(self):
        """ Update the total deliveries of the delivery slot"""
        for rec in self:
            rec.total_delivery = len(rec.delivery_ids or [])

    @api.depends('total_delivery', 'delivery_limit')
    def _compute_remaining_slots(self):
        """Calculate the remaining slots for each delivery slot and deactivate
         the slot if it is full"""
        self.remaining_slots = self.delivery_limit - self.total_delivery
        if self.remaining_slots <= 0:
            self.active = False

    @api.model
    def create(self, vals):
        """Override create method to update delivery_ids"""
        delivery_slot = super(DeliverySlot, self).create(vals)
        delivery_slot.update_delivery_ids()
        return delivery_slot

    def write(self, vals):
        """Override write method to update delivery_ids"""
        if 'delivery_ids' not in vals:
            res = super(DeliverySlot, self).write(vals)
            self.update_delivery_ids()
            return res
        else:
            return super(DeliverySlot, self).write(vals)

    def update_delivery_ids(self):
        """Update the delivery_ids field based on related sale orders"""
        sale_orders = self.env['sale.order'].search(
            [('slot_per_product', '=', True)])
        delivery_orders = sale_orders.filtered(lambda order: any(
            line.slot_id == self.slot_id and line.delivery_date ==
            self.delivery_date
            for line in order.order_line))
        self.delivery_ids = delivery_orders

    def _compute_sale_ids(self):
        """Computing the related sale orders of each delivery slot"""
        for rec in self:
            sale_orders = self.env['sale.order'].search(
                [('slot_per_product', '=', True)])
            delivery_orders = sale_orders.filtered(lambda order: any(
                line.slot_id == rec.slot_id and line.delivery_date ==
                rec.delivery_date
                for line in order.order_line))
            rec.delivery_ids = delivery_orders
