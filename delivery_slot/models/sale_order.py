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


class SaleOrder(models.Model):
    """Inheriting sale order to add boolean field to enable delivery slot"""
    _inherit = 'sale.order'

    @api.model
    def _default_slot_per_product(self):
        """Return the config parameter value for enabling delivery slot."""
        return self.env['ir.config_parameter'].sudo().get_bool(
            'delivery_slot.enable_delivery_date')

    slot_per_product = fields.Boolean(
        string="Delivery Slot per Product",
        default=lambda self: self._default_slot_per_product(),
        help="Enable delivery slot feature")
    delivery_slot_id = fields.Many2one(
        'delivery.slot', help="Delivery slot")
    slot_count = fields.Integer(
        compute='_compute_delivery_slot_count',
        help="Total no of delivery slot related to this sale order")

    def _get_delivery_slots(self):
        """Return the delivery slots used by the lines of this order."""
        self.ensure_one()
        slots = self.env['delivery.slot']
        if not self.slot_per_product:
            return slots
        slot_model = slots.with_context(active_test=False)
        for line in self.order_line.filtered(
                lambda line: line.delivery_date and line.slot_id):
            slots |= slot_model.search([
                ('delivery_date', '=', line.delivery_date),
                ('slot_id', '=', line.slot_id.id)], limit=1)
        return slots

    def action_confirm(self):
        """Confirm the order and link every line to its delivery slot.
        A delivery slot is created when none exists for the chosen date
        and time slot."""
        slot_model = self.env['delivery.slot'].with_context(active_test=False)
        for order in self.filtered('slot_per_product'):
            for line in order.order_line.filtered(
                    lambda line: line.delivery_date and line.slot_id):
                delivery_slot = slot_model.search([
                    ('delivery_date', '=', line.delivery_date),
                    ('slot_id', '=', line.slot_id.id)], limit=1)
                if not delivery_slot:
                    delivery_slot = slot_model.create({
                        'delivery_date': line.delivery_date,
                        'slot_id': line.slot_id.id,
                    })
                line.delivery_slot_id = delivery_slot
        return super().action_confirm()

    @api.depends('slot_per_product', 'order_line.delivery_date',
                 'order_line.slot_id')
    def _compute_delivery_slot_count(self):
        """Returns total number of delivery slots per record"""
        for record in self:
            record.slot_count = len(record._get_delivery_slots())

    def action_view_delivery_slot(self):
        """Returns all delivery slot related to the sale order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Delivery Slots'),
            'view_mode': 'list,form',
            'res_model': 'delivery.slot',
            'domain': [('id', 'in', self._get_delivery_slots().ids)],
            'context': {'create': False, 'active_test': False},
        }


class SaleOrderLine(models.Model):
    """Inheriting sale order line to add slot fields"""
    _inherit = 'sale.order.line'

    delivery_date = fields.Date(
        string="Preferred Delivery Date", help="Delivery date")
    slot_id = fields.Many2one('slot.time', string="Time Slot",
                              help="Delivery time")
    delivery_slot_id = fields.Many2one(
        'delivery.slot', help="Related Delivery Slot")
