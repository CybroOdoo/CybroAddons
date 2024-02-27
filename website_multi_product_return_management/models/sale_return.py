# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class SaleReturn(models.Model):
    """Model for managing return orders."""
    _name = 'sale.return'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = "name"
    _description = "Return Order"

    @api.model
    def _get_default_name(self):
        """Get the default name for a new return order."""
        return self.env['ir.sequence'].get('sale.return')

    active = fields.Boolean(string='Active', default=True,
                            help="Indicates if the return order is active.")
    name = fields.Char(string="Name", default=_get_default_name,
                       help="Name of the return order.")
    sale_order_id = fields.Many2one(
        'sale.order', string="Sale Order",
        required=True,
        help="Reference to the original sale order.")
    partner_id = fields.Many2one(
        'res.partner', string="Customer",
        help="Customer associated with the return order.")
    user_id = fields.Many2one('res.users', string="Responsible",
                              default=lambda self: self.env.user,
                              help="User responsible for the return order.")
    create_date = fields.Datetime(
        string="Create Date",
        help="Date when the return order was created.")
    stock_picking_ids = fields.One2many(
        'stock.picking', 'return_order_pick_id',
        domain="[('return_order_id','=',False)]",
        string="Return Picking",
        help="Shows the return picking of the corresponding return order.")
    picking_count = fields.Integer(compute="_compute_picking_count",
                                   string='Picking Order', copy=False,
                                   default=0, store=True,
                                   help="Count of associated picking orders.")
    delivery_count = fields.Integer(compute="_compute_delivery",
                                    string='Delivery Order', copy=False,
                                    default=0, store=True,
                                    help="Count of associated delivery orders.")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done'),
         ('cancel', 'Canceled')], string='Status', readonly=True,
        default='draft', help="Current state of the return order.")
    source_pick_ids = fields.One2many(
        'stock.picking', 'return_order_id',
        string="Source Delivery",
        domain="[('return_order_pick_id','=',False)]",
        help="Shows the delivery orders of the corresponding return order.")
    note = fields.Text(
        string="Note",
        help="Additional notes or comments for the return order.")

    return_line_ids = fields.One2many(
        'return.order.line', 'order_id',
        string="Return Lines",
        help="Lines associated with the return order.")

    def return_confirm(self):
        """Confirm the sale return"""
        if not self.source_pick_ids:
            stock_picks = self.env['stock.picking'].sudo().search(
                [('origin', '=', self.sale_order_id.name)])
            moves = stock_picks.mapped(
                'move_ids_without_package').sudo().filtered(
                lambda p: p.product_id.id in self.return_line_ids.mapped(
                    'product_id').ids)
        else:
            moves = self.source_pick_ids.mapped(
                'move_ids_without_package').sudo().filtered(
                lambda p: p.product_id.id in self.return_line_ids.mapped(
                    'product_id').ids)

        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            pick = moves[0].picking_id
            vals = {'picking_id': pick.id}
            return_pick_wizard = self.env['stock.return.picking'].sudo().create(
                vals)
            return_pick_wizard._compute_moves_locations()
            return_pick_wizard.product_return_moves.unlink()
            lines = []
            reason = ''
            for line in self.return_line_ids:
                so_line_id = self.sale_order_id.order_line.filtered(
                    lambda m: m.product_template_id ==
                              line.product_id.product_tmpl_id)
                so_line_id.return_order_line_count = line.received_qty
                move = moves.filtered(lambda m: m.product_id == line.product_id)
                lines.append(
                    {'product_id': line.product_id.id,
                     "quantity": line.received_qty,
                     'move_id': move.id, 'to_refund': line.to_refund})
                reason = reason + '\n' + line.reason
            lines = self.env['stock.return.picking.line'].create(lines)
            return_pick_wizard.write({
                'product_return_moves': [(6, 0, lines.ids)]
            })
            return_pick = return_pick_wizard._create_returns()
            if return_pick:
                return_pick = self.env['stock.picking'].sudo().browse(
                    return_pick[0])
                return_pick.update({'note': reason})
                return_pick.write(
                    {'return_order_id': False, 'return_order_pick_id': self.id,
                     'return_order_picking': True})
                self.write({'state': 'confirm'})

    def return_cancel(self):
        """Cancel the return"""
        self.write({'state': 'cancel'})
        if self.stock_picking_ids:
            for rec in self.stock_picking_ids.sudo().filtered(
                    lambda s: s.state not in ['done', 'cancel']):
                rec.action_cancel()

    def _get_report_base_filename(self):
        """Get the base filename for the return order report."""
        self.ensure_one()
        return 'Sale Return - %s' % (self.name)

    def _compute_access_url(self):
        """Compute the access URL for the return order."""
        super(SaleReturn, self)._compute_access_url()
        for order in self:
            order.access_url = '/my/return_orders/%s' % order.id

    @api.depends('stock_picking_ids', 'state')
    def _compute_delivery(self):
        """Function to compute picking and delivery counts"""
        for rec in self:
            rec.delivery_count = 0
            rec.picking_count = 0
            if rec.source_pick_ids:
                rec.delivery_count = len(rec.source_pick_ids)
            else:
                rec.delivery_count = self.env[
                    'stock.picking'].sudo().search_count(
                    [('return_order_id', 'in', self.ids),
                     ('return_order_picking', '=', False)])
            if rec.stock_picking_ids:
                rec.picking_count = len(rec.stock_picking_ids)
            else:
                rec.picking_count = self.env[
                    'stock.picking'].sudo().search_count(
                    [('return_order_pick_id', 'in', self.ids),
                     ('return_order_picking', '=', True)])

    def action_view_picking(self):
        """Function to view the stock picking transfers"""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all")

        pickings = self.mapped('stock_picking_ids')
        if not self.stock_picking_ids:
            pickings = self.env['stock.picking'].sudo().search(
                [('return_order_pick_id', '=', self.id),
                 ('return_order_picking', '=', True)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in
                                               action['views'] if
                                               view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.sudo().filtered(
            lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(
            self._context,
            default_partner_id=self.partner_id.id,
            default_picking_type_id=picking_id.picking_type_id.id)
        return action

    def action_view_delivery(self):
        """Function to view the delivery transfers"""
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.action_picking_tree_all")

        pickings = self.mapped('source_pick_ids')
        if not self.source_pick_ids:
            pickings = self.env['stock.picking'].sudo().search(
                [('return_order_id', '=', self.id),
                 ('return_order_picking', '=', False)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in
                                               action['views'] if
                                               view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(
            lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(
            self._context,
            default_partner_id=self.partner_id.id,
            default_picking_type_id=picking_id.picking_type_id.id)
        return action

    @api.onchange('sale_order_id', 'source_pick_ids')
    def onchange_sale_order_id(self):
        """All the fields are updated according to the sale order"""
        delivery = None
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id

            delivery = self.env['stock.picking'].sudo().search(
                [('origin', '=', self.sale_order_id.name)])
        if self.source_pick_ids:
            delivery = self.source_pick_ids
        if delivery:
            product_ids = delivery.move_ids_without_package.mapped(
                'product_id').ids
            delivery = delivery.ids
        else:
            product_ids = self.sale_order_id.order_line.mapped('product_id').ids

        return {'domain': {'source_pick_ids': [('id', 'in', delivery)],
                           'product_id': [('id', 'in', product_ids)]}}

    @api.onchange('product_id')
    def onchange_product_id(self):
        """Handle changes in the product ID field. and find received quantity"""
        if self.product_id and self.source_pick_ids:
            moves = self.source_pick_ids.mapped(
                'move_ids_without_package').sudo().filtered(
                lambda p: p.product_id == self.product_id)
            if moves:
                self.received_qty = sum(moves.mapped('quantity_done'))


class ReturnOrderLine(models.Model):
    _name = 'return.order.line'
    _description = "Return Products Details"

    order_id = fields.Many2one(
        "sale.return", string="Order",
        help="Reference to the associated sale return order.")
    product_id = fields.Many2one(
        'product.product', string="Product Variant",
        required=True,
        help="Defines the product variant that needs to be returned.")
    product_tmpl_id = fields.Many2one('product.template',
                                      related="product_id.product_tmpl_id",
                                      store=True, string="Product")
    quantity = fields.Float(
        string="Delivered Quantity", store=True,
        help="Quantity originally delivered in the associated sale order.")
    received_qty = fields.Float(
        string="Received Quantity",
        help="Quantity received for the return order.")
    reason = fields.Text(
        "Reason", help="Reason for returning the product.")
    to_refund = fields.Boolean(
        string='Update SO/PO Quantity',
        help='Trigger a decrease of the delivered/received quantity in the'
             ' associated Sale Order/Purchase Order.')
    sale_order_id = fields.Many2one(
        "sale.order", string="Sale Order",
        related="order_id.sale_order_id",
        help="Reference to the associated sale order.")

    @api.onchange('product_id')
    def onchange_product_id(self):
        """ setting up domain for products as per the products in the
         vendor price list"""
        self.ensure_one()
        if self._context.get('order_id'):
            order_id = self.env['sale.order'].browse(
                self._context.get('order_id'))
            products = order_id.order_line.mapped('product_id').ids
            if self.product_id:
                qty = sum(
                    order_id.order_line.filtered(
                        lambda p: p.product_id == self.product_id).mapped(
                        'qty_delivered'))
                self.quantity = qty
            return {'domain': {'product_id': [('id', 'in', products)]}}
