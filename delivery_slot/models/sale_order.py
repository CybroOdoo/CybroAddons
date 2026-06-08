# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Technologies (odoo@cybrosys.com)
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
from odoo import _, fields, models
# from odoo.addons.sale_stock.models.sale_order_line import SaleOrderLine


class SaleOrder(models.Model):
    """Inheriting sale order to add boolean field to enable delivery slot"""
    _inherit = 'sale.order'

    slot_per_product = fields.Boolean(
        string="Delivery Slot per Product",
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param(
            'delivery_slot.enable_delivery_date'),
        help="Enable delivery slot feature")
    delivery_slot_id = fields.Many2one('delivery.slot', string='Delivery Slot',
                                       help="Delivery slot")
    slot_count = fields.Integer(
        string='Slot Count', compute='_compute_delivery_slot_count',
        help="Total no of delivery slot related to this sale order")

    def action_confirm(self):
        """Confirm the order and update delivery slot information.
            If `slot_per_product` is enabled, for each order line, the
            corresponding delivery slot is searched in the system.
            If found, the total delivery count is incremented. If not found,
            a new delivery slot is created with a delivery count of 1.
            :return: The result of the super method `action_confirm()`."""
        if self.slot_per_product:
            for line in self.order_line:
                delivery_slot = self.env['delivery.slot'].search(
                    [('delivery_date', '=', line.delivery_date),
                     ('slot_id', '=', line.slot_id.id),
                     ('active', '=', True)])
                if delivery_slot:
                    delivery_slot.total_delivery += 1
                    if delivery_slot.remaining_slots <= 0:
                        delivery_slot.active = False
                else:
                    if line.slot_id and line.delivery_date:
                        self.env['delivery.slot'].create({
                            'delivery_date': line.delivery_date,
                            'slot_id': line.slot_id.id,
                            'total_delivery': 1,
                        })
        return super().action_confirm()

    def _compute_delivery_slot_count(self):
        """Returns total number of delivery slots per record"""
        for record in self:
            if record.slot_per_product:
                recs = {
                    slot_record.id
                    for line in record.order_line
                    if line.delivery_date
                    for slot_record in self.env['delivery.slot'].search([
                        ('delivery_date', '=', line.delivery_date),
                        ('slot_id', '=', line.slot_id.id),
                        ('active', '=', True)], limit=1)
                }
                record.slot_count = len(recs)
            else:
                record.slot_count = 0

    def action_view_delivery_slot(self):
        """Returns all delivery slot related to the sale order"""
        rec = [
            slot_record.id
            for record in self
            if record.slot_per_product
            for line in record.order_line
            for slot_record in self.env['delivery.slot'].search([
                ('delivery_date', '=', line.delivery_date or self.date_order),
                ('slot_id', '=', line.slot_id.id),
                ('active', '=', True)], limit=1)
        ]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery Slots',
            'view_mode': 'list,form',
            'res_model': 'delivery.slot',
            'domain': [('id', 'in', rec)],
            'context': "{'create': False}"
        }


class SaleOrderLine(models.Model):
    """Inheriting sale order line to add slot fields"""
    _inherit = 'sale.order.line'

    delivery_date = fields.Date(string="Delivery Date", help="Delivery date")
    slot_id = fields.Many2one('slot.time', string="Time Slot",
                              help="Delivery time")
    delivery_slot_id = fields.Many2one(
        'delivery.slot', string='Delivery Slot', help="Related Delivery Slot")
