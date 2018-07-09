# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.tools import float_is_zero


class PosReconciliation(models.Model):
    _inherit = "pos.order"

    @api.model
    def _process_order(self, pos_order):
        prec_acc = self.env['decimal.precision'].precision_get('Account')
        pos_session = self.env['pos.session'].browse(pos_order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            pos_order['pos_session_id'] = self._get_valid_session(pos_order).id
        order = self.create(self._order_fields(pos_order))
        journal_ids = set()
        payment_sum = 0
        for payments in pos_order['statement_ids']:
            if not float_is_zero(payments[2]['amount'], precision_digits=prec_acc):
                payment_sum = payment_sum + payments[2]['amount']
                if payment_sum > pos_order['amount_total']:
                    payments[2]['amount'] = payments[2]['amount'] - pos_order['amount_return']
                order.add_payment(self._payment_fields(payments[2]))
            journal_ids.add(payments[2]['journal_id'])
        if pos_session.sequence_number <= pos_order['sequence_number']:
            pos_session.write({'sequence_number': pos_order['sequence_number'] + 1})
            pos_session.refresh()
        return order
