# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class SaleReturn(models.Model):
    """Return order raised against a delivered sale order"""
    _name = 'sale.return'
    _inherit = ['portal.mixin']
    _order = 'name desc'
    _description = 'Return Order'

    @api.model
    def _get_default_name(self):
        # ir.sequence.next_by_code() gates on read access to ir.sequence
        # itself, which portal users never have; drawing a number is not
        # a business-data concern, so this is scoped to just this call.
        return self.env['ir.sequence'].sudo().next_by_code('sale.return')

    active = fields.Boolean(default=True, help='Is active or not')
    name = fields.Char(default=lambda self: self._get_default_name(),
                       copy=False, help='Name of return order')
    product_id = fields.Many2one(
        'product.product', string='Product Variant', required=True,
        domain="[('id', 'in', available_product_ids)]",
        help='Product variant that needs to be returned')
    product_tmpl_id = fields.Many2one(
        'product.template', related='product_id.product_tmpl_id',
        store=True, string='Product', help='Return product')
    sale_order_id = fields.Many2one('sale.order', required=True,
                                    help='Reference of the sale order')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 compute='_compute_partner_id', store=True,
                                 readonly=False, precompute=True,
                                 help='Customer of the return order')
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user,
                              help='Responsible user for the return order')
    quantity = fields.Float(default=1.0, help='Return quantity')
    received_qty = fields.Float(string='Received Quantity',
                                help='Received item quantity')
    reason = fields.Text(help='Reason of the return')
    return_picking_ids = fields.One2many(
        'stock.picking', 'return_order_pick_id',
        domain="[('return_order_id', '=', False)]",
        help='Return pickings of this return order')
    source_picking_ids = fields.One2many(
        'stock.picking', 'return_order_id', string='Source Delivery',
        domain="[('return_order_pick_id', '=', False)]",
        help='Delivery orders of this return order')
    available_product_ids = fields.Many2many(
        'product.product', compute='_compute_available_ids',
        help='Products that can be returned for the selected sale order')
    available_picking_ids = fields.Many2many(
        'stock.picking', compute='_compute_available_ids',
        help='Deliveries of the selected sale order')
    picking_count = fields.Integer(compute='_compute_picking_counts',
                                   string='Picking Order',
                                   help='Number of return pickings')
    delivery_count = fields.Integer(compute='_compute_picking_counts',
                                    string='Delivery Order',
                                    help='Number of source deliveries')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done'),
         ('cancel', 'Cancelled')],
        string='Status', readonly=True, default='draft',
        help='Status of return order')
    note = fields.Text(help='Internal note')
    to_refund = fields.Boolean(
        string='Update SO/PO Quantity',
        help='Trigger a decrease of the delivered/received quantity in the '
             'associated Sale Order/Purchase Order')

    @api.constrains('quantity')
    def _check_quantity(self):
        """A return must be for a positive quantity"""
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(
                    self.env._("The return quantity must be greater than zero."))

    @api.depends('sale_order_id')
    def _compute_partner_id(self):
        """Default the customer from the sale order"""
        for rec in self:
            if rec.sale_order_id:
                rec.partner_id = rec.sale_order_id.partner_id

    @api.depends('sale_order_id', 'source_picking_ids')
    def _compute_available_ids(self):
        """Deliveries and products the return can be made from"""
        for rec in self:
            deliveries = rec.sale_order_id._get_return_source_pickings()
            rec.available_picking_ids = deliveries
            pickings = rec.source_picking_ids or deliveries
            if pickings:
                rec.available_product_ids = pickings.move_ids.product_id
            else:
                rec.available_product_ids = (
                    rec.sale_order_id.order_line.product_id)

    @api.depends('source_picking_ids', 'return_picking_ids')
    def _compute_picking_counts(self):
        """Count the source deliveries and the return pickings"""
        for rec in self:
            rec.delivery_count = len(rec.source_picking_ids)
            rec.picking_count = len(rec.return_picking_ids)

    @api.model
    def _get_returnable_qty(self, sale_order, product):
        """Delivered quantity of a product that is not already covered by an
        open (draft or confirmed) return order"""
        delivered = sum(sale_order.order_line.filtered(
            lambda line: line.product_id == product).mapped('qty_delivered'))
        pending = sum(self.sudo().search([
            ('sale_order_id', '=', sale_order.id),
            ('product_id', '=', product.id),
            ('state', 'in', ('draft', 'confirm')),
        ]).mapped('quantity'))
        return delivered - pending

    def _get_return_moves(self):
        """Delivery moves of the returned product, validated ones first"""
        self.ensure_one()
        pickings = (self.source_picking_ids
                    or self.sale_order_id._get_return_source_pickings())
        moves = pickings.move_ids.filtered(
            lambda move: move.product_id == self.product_id)
        return moves.sorted(
            lambda move: (move.picking_id.state == 'done',
                          move.product_uom_qty),
            reverse=True)

    def return_confirm(self):
        """Confirm the return and create the return picking"""
        for rec in self:
            moves = rec._get_return_moves()
            if not moves:
                raise UserError(
                    self.env._("No delivery of %s was found for this sale order.",
                      rec.product_id.display_name))
            pick = moves[0].picking_id
            if pick.state != 'done':
                raise UserError(
                    self.env._("You cannot return from a transfer (%s) that has not "
                      "been validated yet.", pick.name))
            return_pick = pick._create_return()
            target_move = return_pick.move_ids.filtered(
                lambda m: m.origin_returned_move_id == moves[0])
            if not target_move:
                return_pick.unlink()
                raise UserError(
                    self.env._("Could not create a return for %(product)s on "
                      "transfer %(picking)s.",
                      product=rec.product_id.display_name,
                      picking=pick.name))
            (return_pick.move_ids - target_move).unlink()
            target_move.write({
                'product_uom_qty': rec.quantity,
                'to_refund': rec.to_refund,
            })
            return_pick.write({
                'note': rec.reason,
                'return_order_id': False,
                'return_order_pick_id': rec.id,
                'return_order_picking': True,
            })
            rec.write({'state': 'confirm'})

    def return_cancel(self):
        """Cancel the return and its open return pickings"""
        self.write({'state': 'cancel'})
        self.return_picking_ids.filtered(
            lambda picking: picking.state not in ('done', 'cancel')
        ).action_cancel()

    def _get_report_base_filename(self):
        """Base name of the return order report"""
        self.ensure_one()
        return 'Sale Return - %s' % self.name

    def _compute_access_url(self):
        """Portal URL of the return order"""
        for order in self:
            order.access_url = '/my/return_orders/%s' % order.id

    def _action_view_pickings(self, pickings):
        """Open the given pickings, in a form view when there is only one"""
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id(
            'stock.action_picking_tree_all')
        if len(pickings) == 1:
            action['views'] = [
                (self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action['domain'] = [('id', 'in', pickings.ids)]
        action['context'] = dict(
            self.env.context,
            default_partner_id=self.partner_id.id,
            default_picking_type_id=pickings[:1].picking_type_id.id,
            create=False)
        return action

    def action_view_picking(self):
        """Open the return pickings"""
        return self._action_view_pickings(self.return_picking_ids)

    def action_view_delivery(self):
        """Open the source deliveries"""
        return self._action_view_pickings(self.source_picking_ids)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Show the quantity delivered for the selected product"""
        if self.product_id and self.source_picking_ids:
            moves = self.source_picking_ids.move_ids.filtered(
                lambda p: p.product_id == self.product_id)
            if moves:
                self.received_qty = sum(moves.mapped('quantity'))
