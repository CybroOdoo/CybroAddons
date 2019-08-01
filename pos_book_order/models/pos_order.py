# -*- coding: utf-8 -*-
import logging
import psycopg2
from odoo import models, fields, api, tools

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    """Inherited model for pos order,all confirmed booking orders are converted as pos orders"""
    _inherit = 'pos.order'

    booking_ref = fields.Many2one('book.order', string='Booking Ref')
    delivery_address = fields.Char('Delivery Address', help='Address of customer for delivery')
    phone = fields.Char('Contact no', help='Phone of customer for delivery')

    @api.model
    def create_from_ui(self, orders):
        """Method to create pos order"""
        references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        order_ids = []
        quot_ids = []
        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)
            pos_order = self._process_order(order)
            if pos_order.booking_ref:
                pos_order.booking_ref.write({'state': 'confirmed'})
                quot_ids.append(pos_order.booking_ref.id)
            order_ids.append(pos_order.id)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                pos_order.action_pos_order_invoice()
                pos_order.invoice_id.sudo().action_invoice_open()
                pos_order.account_move = pos_order.invoice_id.move_id
        return order_ids, quot_ids

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        quot_id = False
        if 'quotation_ref' in ui_order:
            if ui_order['quotation_ref']:
                quot_id = ui_order.get('quotation_ref')['id']
        order_fields['booking_ref'] = quot_id
        return order_fields