# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shijin V (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################


from odoo import models, fields, api, _


class ReturnOrder(models.Model):
    _name = 'sale.return'
    _inherit = ['portal.mixin']
    _rec_name = "name"
    _order = "name"
    _description = "Return Order"

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('sale.return')

    active = fields.Boolean('Active', default=True)
    name = fields.Char(string="Name", default=_get_default_name)
    sale_order = fields.Many2one('sale.order', string="Sale Order", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    create_date = fields.Datetime(string="Create Date")
    stock_picking = fields.One2many('stock.picking', 'return_order_pick', domain="[('return_order','=',False)]",
                                    string="Return Picking",
                                    help="Shows the return picking of the corresponding return order")
    picking_count = fields.Integer(compute="_compute_delivery", string='Picking Order', copy=False, default=0,
                                   store=True)
    delivery_count = fields.Integer(compute="_compute_delivery", string='Delivery Order', copy=False, default=0,
                                    store=True)
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done'), ('cancel', 'Canceled')],
                             string='Status', readonly=True, default='draft')
    source_pick = fields.One2many('stock.picking', 'return_order', string="Source Delivery",
                                  domain="[('return_order_pick','=',False)]",
                                  help="Shows the delivery orders of the corresponding return order")
    note = fields.Text("Note")

    return_line_ids = fields.One2many('return.order.line', 'order_id', string="Return Lines")

    def return_confirm(self):
        """Confirm the sale return"""
        if not self.source_pick:
            stock_picks = self.env['stock.picking'].sudo().search([('origin', '=', self.sale_order.name)])
            moves = stock_picks.mapped('move_ids_without_package').sudo().filtered(
                lambda p: p.product_id.id in self.return_line_ids.mapped('product_id').ids)
        else:
            moves = self.source_pick.mapped('move_ids_without_package').sudo().filtered(
                lambda p: p.product_id.id in self.return_line_ids.mapped('product_id').ids)

        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            pick = moves[0].picking_id
            vals = {'picking_id': pick.id}
            return_pick_wizard = self.env['stock.return.picking'].sudo().create(vals)
            return_pick_wizard._onchange_picking_id()
            return_pick_wizard.product_return_moves.unlink()
            lines = []
            reason = ''
            for line in self.return_line_ids:
                move = moves.filtered(lambda m:m.product_id == line.product_id)
                lines.append(
                    {'product_id': line.product_id.id, "quantity": line.received_qty,
                     'move_id': move.id, 'to_refund': line.to_refund})
                reason = reason + '\n' + line.reason
            lines = self.env['stock.return.picking.line'].create(lines)
            return_pick_wizard.write({
                'product_return_moves': [(6, 0, lines.ids)]
            })
            return_pick = return_pick_wizard._create_returns()
            if return_pick:
                return_pick = self.env['stock.picking'].sudo().browse(return_pick[0])
                return_pick.update({'note': reason})
                return_pick.write({'return_order': False, 'return_order_pick': self.id, 'return_order_picking': True})
                self.write({'state': 'confirm'})

    def return_cancel(self):
        """Cancel the return"""
        self.write({'state': 'cancel'})
        if self.stock_picking:
            for rec in self.stock_picking.sudo().filtered(lambda s: s.state not in ['done', 'cancel']):
                rec.action_cancel()

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Sale Return - %s' % (self.name)

    def _compute_access_url(self):
        super(ReturnOrder, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/return_orders/%s' % order.id

    @api.depends('stock_picking', 'state')
    def _compute_delivery(self):
        """Function to compute picking and delivery counts"""
        for rec in self:
            rec.delivery_count = 0
            rec.picking_count = 0
            if rec.source_pick:
                rec.delivery_count = len(rec.source_pick)
            else:
                rec.delivery_count = self.env['stock.picking'].sudo().search_count(
                    [('return_order', 'in', self.ids), ('return_order_picking', '=', False)])
            if rec.stock_picking:
                rec.picking_count = len(rec.stock_picking)
            else:
                rec.picking_count = self.env['stock.picking'].sudo().search_count(
                    [('return_order_pick', 'in', self.ids), ('return_order_picking', '=', True)])

    def action_view_picking(self):
        """Function to view the stock picking transfers"""
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        pickings = self.mapped('stock_picking')
        if not self.stock_picking:
            pickings = self.env['stock.picking'].sudo().search(
                [('return_order_pick', '=', self.id), ('return_order_picking', '=', True)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.sudo().filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id=self.partner_id.id,
                                 default_picking_type_id=picking_id.picking_type_id.id)
        return action

    def action_view_delivery(self):
        """Function to view the delivery transfers"""
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        pickings = self.mapped('source_pick')
        if not self.source_pick:
            pickings = self.env['stock.picking'].sudo().search(
                [('return_order', '=', self.id), ('return_order_picking', '=', False)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id=self.partner_id.id,
                                 default_picking_type_id=picking_id.picking_type_id.id)
        return action

    @api.onchange('sale_order', 'source_pick')
    def onchange_sale_order(self):
        """All the fields are updated according to the sale order"""
        delivery = None
        if self.sale_order:
            self.partner_id = self.sale_order.partner_id

            delivery = self.env['stock.picking'].sudo().search([('origin', '=', self.sale_order.name)])
        if self.source_pick:
            delivery = self.source_pick
        if delivery:
            product_ids = delivery.move_ids_without_package.mapped('product_id').ids
            delivery = delivery.ids
        else:
            product_ids = self.sale_order.order_line.mapped('product_id').ids

        return {'domain': {'source_pick': [('id', 'in', delivery)], 'product_id': [('id', 'in', product_ids)]}}

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id and self.source_pick:
            moves = self.source_pick.mapped('move_ids_without_package').sudo().filtered(
                lambda p: p.product_id == self.product_id)
            if moves:
                self.received_qty = sum(moves.mapped('quantity_done'))


class ReturnOrderLine(models.Model):
    _name = 'return.order.line'
    _description = "return products Details"

    order_id = fields.Many2one("sale.return", string="Order")
    product_id = fields.Many2one('product.product', string="Product Variant", required=True,
                                 help="defines the product variant that need to be returned")
    product_tmpl_id = fields.Many2one('product.template', related="product_id.product_tmpl_id", store=True,
                                      string="Product")
    quantity = fields.Float(string="Delivered Quantity", store=True)
    received_qty = fields.Float(string="Received Quantity")
    reason = fields.Text("Reason")
    to_refund = fields.Boolean(string='Update SO/PO Quantity',
                               help='Trigger a decrease of the delivered/received quantity in'
                                    ' the associated Sale Order/Purchase Order')

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ setting up domain for products as per the products in the vendor price list"""
        self.ensure_one()
        if self._context.get('order_id'):
            order_id = self.env['sale.order'].browse(self._context.get('order_id'))

            products = order_id.order_line.mapped('product_id').ids
            if self.product_id:
                dqty = sum(
                    order_id.order_line.filtered(lambda p: p.product_id == self.product_id).mapped('qty_delivered'))

                self.quantity = dqty
            return {'domain': {'product_id': [('id', 'in', products)]}}
