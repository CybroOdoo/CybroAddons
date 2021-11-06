# -*- coding: utf-8 -*-
from odoo import models, api, fields


class PosReturn(models.Model):
    _inherit = 'pos.order'

    return_ref = fields.Char(string='Return Ref', readonly=True, copy=False)
    return_status = fields.Selection([
        ('nothing_return', 'Nothing Returned'),
        ('partialy_return', 'Partialy Returned'),
        ('fully_return', 'Fully Returned')
    ], string="Return Status", default='nothing_return',
        help="Return status of Order")

    @api.model
    def get_lines(self, ref):
        result = []
        order_id = self.search([('pos_reference', '=', ref)], limit=1)
        if order_id:
            lines = self.env['pos.order.line'].search([('order_id', '=', order_id.id)])
            for line in lines:
                if line.qty - line.returned_qty > 0:
                    new_vals = {
                        'product_id': line.product_id.id,
                        'product': line.product_id.name,
                        'qty': line.qty - line.returned_qty,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'line_id': line.id,
                    }
                    result.append(new_vals)

        return [result]

    @api.model
    def get_client(self, ref):
        order_id = self.search([('pos_reference', '=', ref)], limit=1)
        client = ''
        if order_id:
            client = order_id.partner_id.id
        return client

    def _order_fields(self, ui_order):
        order = super(PosReturn, self)._order_fields(ui_order)
        if ui_order['lines']:
            for data in ui_order['lines']:
                if data[2]['line_id']:
                    line = self.env['pos.order.line'].search([('id', '=', data[2]['line_id'])])
                    if line:
                        qty = -(data[2]['qty'])
                        line.returned_qty += qty
        if 'return_ref' in ui_order.keys() and ui_order['return_ref']:
            order['return_ref'] = ui_order['return_ref']
            parent_order = self.search([('pos_reference', '=', ui_order['return_ref'])], limit=1)
            lines = self.env['pos.order.line'].search([('order_id', '=', parent_order.id)])
            ret = 0
            qty = 0
            for line in lines:
                qty += line.qty
                if line.returned_qty:
                    ret += 1
            if qty-ret == 0:
                if parent_order:
                    parent_order.return_status = 'fully_return'
            elif ret:
                if qty > ret:
                    if parent_order:
                        parent_order.return_status = 'partialy_return'
        return order

    @api.model
    def get_status(self, ref):
        order_id = self.search([('pos_reference', '=', ref)], limit=1)
        if order_id.return_status == 'fully_return':
            return False
        else:
            return True


class NewPosLines(models.Model):
    _inherit = "pos.order.line"

    returned_qty = fields.Integer(string='Returned', digits=0)
