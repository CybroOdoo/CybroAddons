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
    product_id = fields.Many2one('product.product', string="Product Variant", required=True,
                                 help="defines the product variant that need to be returned")
    product_tmpl_id = fields.Many2one('product.template', related="product_id.product_tmpl_id", store=True,
                                      string="Product")
    sale_order = fields.Many2one('sale.order', string="Sale Order", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    create_date = fields.Datetime(string="Create Date")
    quantity = fields.Float(string="Quantity", default=0)
    received_qty = fields.Float(string="Received Quantity")
    reason = fields.Text("Reason")
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
    to_refund = fields.Boolean(string='Update SO/PO Quantity',
                                          help='Trigger a decrease of the delivered/received quantity in'
                                               ' the associated Sale Order/Purchase Order')

    def return_confirm(self):
        """Confirm the sale return"""
        if not self.source_pick:
            stock_picks = self.env['stock.picking'].search([('origin', '=', self.sale_order.name)])
            moves = stock_picks.mapped('move_ids_without_package').filtered(lambda p: p.product_id == self.product_id)
        else:
            moves = self.source_pick.mapped('move_ids_without_package').filtered(
                lambda p: p.product_id == self.product_id)
        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            pick = moves[0].picking_id
            vals = {'picking_id': pick.id}
            return_pick_wizard = self.env['stock.return.picking'].create(vals)
            return_pick_wizard._onchange_picking_id()
            return_pick_wizard.product_return_moves.unlink()
            lines = {'product_id': self.product_id.id, "quantity": self.quantity, 'wizard_id': return_pick_wizard.id,
                     'move_id': moves[0].id, 'to_refund': self.to_refund}
            self.env['stock.return.picking.line'].create(lines)
            return_pick = return_pick_wizard._create_returns()
            if return_pick:
                return_pick = self.env['stock.picking'].browse(return_pick[0])
                return_pick.update({'note': self.reason})
                return_pick.write({'return_order': False, 'return_order_pick': self.id, 'return_order_picking': True})
                self.write({'state': 'confirm'})

    def return_cancel(self):
        """Cancel the return"""
        self.write({'state': 'cancel'})
        if self.stock_picking:
            for rec in self.stock_picking.filtered(lambda s: s.state not in ['done', 'cancel']):
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
                rec.delivery_count = self.env['stock.picking'].search_count(
                    [('return_order', 'in', self.ids), ('return_order_picking', '=', False)])
            if rec.stock_picking:
                rec.picking_count = len(rec.stock_picking)
            else:
                rec.picking_count = self.env['stock.picking'].search_count(
                    [('return_order_pick', 'in', self.ids), ('return_order_picking', '=', True)])

    def action_view_picking(self):
        """Function to view the stock picking transfers"""
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        pickings = self.mapped('stock_picking')
        if not self.stock_picking:
            pickings = self.env['stock.picking'].search(
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
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
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

        pickings = self.mapped('stock_picking')
        if not self.stock_picking:
            pickings = self.env['stock.picking'].search(
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

            delivery = self.env['stock.picking'].search([('origin', '=', self.sale_order.name)])
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
            moves = self.source_pick.mapped('move_ids_without_package').filtered(
                lambda p: p.product_id == self.product_id)
            if moves:
                self.received_qty = sum(moves.mapped('quantity_done'))
