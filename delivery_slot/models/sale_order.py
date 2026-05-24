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
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.sale_stock.models.sale_order_line import SaleOrderLine


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
                delivery_slot = self.env['delivery.slot'].with_context(
                    active_test=False).search(
                    [('delivery_date', '=', line.delivery_date),
                     ('slot_id', '=', line.slot_id.id)], limit=1)
                if delivery_slot:
                    if not delivery_slot.active:
                        raise ValidationError(
                            "The delivery slot %s on %s is not available."
                            % (line.slot_id.name, line.delivery_date))
                    if delivery_slot.remaining_slots <= 0:
                        raise ValidationError(
                            "The delivery slot %s on %s has reached its "
                            "limit." % (line.slot_id.name, line.delivery_date))
                else:
                    if line.slot_id and line.delivery_date:
                        self.env['delivery.slot'].create({
                            'delivery_date': line.delivery_date,
                            'slot_id': line.slot_id.id,
                        })
        return super().action_confirm()

    def _compute_delivery_slot_count(self):
        """Returns total number of delivery slots per record"""
        for record in self:
            if record.slot_per_product and record.state in ('sale', 'done'):
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
            if record.slot_per_product and record.state in ('sale', 'done')
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



    @api.constrains('delivery_date')
    def _check_delivery_date(self):
        """Constraint to prevent selecting past dates for delivery"""
        for line in self:
            if line.delivery_date and line.delivery_date < fields.Date.today():
                raise ValidationError("You cannot select a past date for delivery.")

    @api.constrains('slot_id', 'delivery_date')
    def _check_delivery_slot_limit(self):
        """Constraint to prevent saving when the delivery slot has reached its limit."""
        for line in self:
            if line.slot_id and line.delivery_date:
                delivery_slot = self.env['delivery.slot'].with_context(
                    active_test=False).search([
                    ('delivery_date', '=', line.delivery_date),
                    ('slot_id', '=', line.slot_id.id),
                ], limit=1)
                if delivery_slot and not delivery_slot.active:
                    raise ValidationError(
                        "The delivery slot '%s' on %s is not available."
                        % (line.slot_id.name, line.delivery_date))
                if delivery_slot and delivery_slot.remaining_slots <= 0:
                    raise ValidationError(
                        "The delivery slot '%s' on %s has reached its limit. "
                        "Please select a different slot or date."
                        % (line.slot_id.name, line.delivery_date))

    @api.onchange('slot_id', 'delivery_date')
    def _onchange_slot_id_date(self):
        """Onchange to show warning and filter available slots"""
        domain = []
        if self.delivery_date:
            delivery_slots = self.env['delivery.slot'].with_context(
                active_test=False).search([
                ('delivery_date', '=', self.delivery_date),
            ])
            unavailable_slot_ids = [
                rec.slot_id.id for rec in delivery_slots
                if not rec.active or rec.remaining_slots <= 0]
            domain = [('id', 'not in', unavailable_slot_ids)]
        
        res = {'domain': {'slot_id': domain}}
        
        if self.slot_id and self.delivery_date:
            delivery_slot = self.env['delivery.slot'].with_context(
                active_test=False).search([
                ('delivery_date', '=', self.delivery_date),
                ('slot_id', '=', self.slot_id.id),
            ], limit=1)
            if delivery_slot and not delivery_slot.active:
                res['warning'] = {
                    'title': "Delivery Slot",
                    'message': "The delivery slot %s on %s is not available."
                               % (self.slot_id.name, self.delivery_date),
                }
                self.slot_id = False
            elif delivery_slot and delivery_slot.remaining_slots <= 0:
                res['warning'] = {
                    'title': "Delivery Limit",
                    'message': "The delivery slot %s on %s has reached its limit."
                               % (self.slot_id.name, self.delivery_date),
                }
        return res

    def _prepare_procurement_values(self, group_id=False):
        """ Prepare specific key for moves or other components that will be
        created from a stock rule coming from a sale order line. This method
        could be overridden in order to add other custom key that could
        be used in move/po creation.
        """
        date_deadline = self.delivery_date or (
                self.order_id.date_order + timedelta(
            days=self.customer_lead or 0.0))
        date_planned = date_deadline - timedelta(
            days=self.order_id.company_id.security_lead)
        values = {
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned,
            'date_deadline': date_deadline,
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'product_description_variants': self.with_context(
                lang=self.order_id.partner_id.lang).
            _get_sale_order_line_multiline_description_variants(),
            'company_id': self.order_id.company_id,
            'product_packaging_id': self.product_packaging_id,
            'sequence': self.sequence,
        }
        if self.order_id.slot_per_product:
            values.update({"slot_per_product": 'True'})
            if self.slot_id:
                values.update({'slot_time_id': self.slot_id.id})
        return values
    SaleOrderLine._prepare_procurement_values = _prepare_procurement_values
