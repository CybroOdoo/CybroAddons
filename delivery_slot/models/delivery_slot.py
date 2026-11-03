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


class DeliverySlot(models.Model):
    """Delivery slot model"""
    _name = 'delivery.slot'
    _description = 'Delivery slot'
    _rec_name = 'delivery_date'

    delivery_date = fields.Date(
        default=fields.Date.today, help="Choose a delivery date")
    slot_id = fields.Many2one('slot.time', help="Choose Delivery slot")
    delivery_ids = fields.One2many(
        'sale.order', 'delivery_slot_id',
        compute="_compute_delivery_ids", help="Related Deliveries")
    delivery_limit = fields.Integer(
        default=100, help="Limit of this delivery slot")
    total_delivery = fields.Integer(
        string="Total No of Deliveries", compute='_compute_total_delivery',
        help="Current deliveries in this slot")
    remaining_slots = fields.Integer(
        string="Available No of Deliveries",
        compute='_compute_remaining_slots',
        help="Remaining no of deliveries in this slot")
    active = fields.Boolean(default=True, help="Active or not")

    @api.depends('slot_id', 'delivery_date')
    def _compute_delivery_ids(self):
        """Compute the sale orders that use this delivery slot"""
        order_line = self.env['sale.order.line']
        for rec in self:
            lines = order_line.search([
                ('slot_id', '=', rec.slot_id.id),
                ('delivery_date', '=', rec.delivery_date),
                ('order_id.slot_per_product', '=', True)])
            rec.delivery_ids = lines.order_id

    @api.depends('delivery_ids')
    def _compute_total_delivery(self):
        """Update the total deliveries of the delivery slot"""
        for rec in self:
            rec.total_delivery = len(rec.delivery_ids)

    @api.depends('total_delivery', 'delivery_limit')
    def _compute_remaining_slots(self):
        """Calculate the remaining deliveries available in the slot"""
        for rec in self:
            rec.remaining_slots = rec.delivery_limit - rec.total_delivery
