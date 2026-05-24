# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Manasa T P (odoo@cybrosys.com)
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
    slot_id = fields.Many2one('slot.time', string="Slot",
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

    _sql_constraints = [
        ('delivery_date_slot_unique', 'unique(delivery_date, slot_id)',
         'A delivery slot already exists for this date and time slot!')
    ]

    def _get_pending_delivery_orders(self):
        """Return sale orders with undelivered lines for this delivery slot."""
        self.ensure_one()
        if not self.delivery_date or not self.slot_id:
            return self.env['sale.order']
        order_lines = self.env['sale.order.line'].search([
            ('order_id.slot_per_product', '=', True),
            ('delivery_date', '=', self.delivery_date),
            ('slot_id', '=', self.slot_id.id),
            ('state', 'not in', ('cancel', 'draft')),
        ]).filtered(
            lambda line: line.qty_delivered < line.product_uom_qty)
        return order_lines.mapped('order_id')

    def _compute_total_delivery(self):
        """ Update the total deliveries of the delivery slot"""
        for rec in self:
            rec.total_delivery = len(rec._get_pending_delivery_orders())

    @api.depends('total_delivery', 'delivery_limit')
    def _compute_remaining_slots(self):
        """Calculate the remaining slots for each delivery slot"""
        for record in self:
            record.remaining_slots = record.delivery_limit - record.total_delivery

    def _compute_sale_ids(self):
        """Compute sale orders that still reserve this delivery slot."""
        for rec in self:
            rec.delivery_ids = rec._get_pending_delivery_orders()
