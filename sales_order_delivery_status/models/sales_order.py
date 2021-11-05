# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    delivery_status = fields.Selection(selection=[
        ('nothing', 'Nothing to Deliver'), ('to_deliver', 'To Deliver'),
        ('partial', 'Partially Deliver'), ('delivered', 'Delivered'),
        ('processing', 'Processing')
    ], string='Delivery Status', compute='_compute_delivery_status', store=True,
        readonly=True, copy=False, default='nothing')

    @api.depends('state', 'order_line.qty_delivered')
    def _compute_delivery_status(self):
        for rec in self:
            pickings = self.env['stock.picking'].search([('sale_id', '=', rec.id)])
            orderlines = rec.mapped('order_line').filtered(lambda x:x.product_id.type != 'service')
            service_orderlines =  rec.mapped('order_line').filtered(lambda x:x.product_id.type == 'service')
            if not pickings and not service_orderlines:
                rec.delivery_status = 'nothing'
            elif all(o.qty_delivered == 0 for o in orderlines):
                rec.delivery_status = 'to_deliver'
            elif orderlines.filtered(lambda x: x.qty_delivered < x.product_uom_qty):
                rec.delivery_status = 'partial'
            elif all(o.qty_delivered == o.product_uom_qty for o in orderlines):
                rec.delivery_status = 'delivered'
            elif any(p.state in ('waiting', 'confirmed') for p in pickings):
                rec.delivery_status = 'processing'
            if not orderlines and service_orderlines and rec.state == 'sale':
                rec.delivery_status = 'delivered'
