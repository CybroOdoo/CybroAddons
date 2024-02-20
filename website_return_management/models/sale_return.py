# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class SaleReturn(models.Model):
    _name = 'sale.return'
    _inherit = ['portal.mixin']
    _rec_name = "name"
    _order = "name"
    _description = "Sale Return"

    @api.model
    def _get_default_name(self):
        """Default value for name field"""
        return self.env['ir.sequence'].get('sale.return')

    active = fields.Boolean('Active', default=True,
                            help="Show Active Record")
    name = fields.Char(string="Name", default=_get_default_name,
                       help="Name Field")
    product_id = fields.Many2one('product.product',
                                 string="Product Variant", required=True,
                                 help="defines the product variant that need"
                                      "to be returned")
    product_tmpl_id = fields.Many2one('product.template',
                                      related="product_id.product_tmpl_id",
                                      store=True,
                                      string="Product",
                                      help="Product template relation")
    sale_order_id = fields.Many2one('sale.order',
                                    string="Sale Order",
                                    required=True, help="Sale order relation")
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="Res partner relation")
    user_id = fields.Many2one('res.users', string="Responsible",
                              default=lambda self: self.env.user,
                              help="Res user relation")
    create_date = fields.Datetime(string="Create Date", help="Create Date")
    quantity = fields.Float(string="Quantity", default=0,
                            help="Number of quantity")
    received_qty = fields.Float(string="Received Quantity",
                                help="Number of received quantity")
    reason = fields.Text("Reason", help="Reason to add")
    stock_picking_ids = fields.One2many('stock.picking',
                                        'return_order_pick_id',
                                        domain="["
                                               "('return_order_id','=',False)]",
                                        string="Return Picking",
                                        help="Shows the return picking of the "
                                             "corresponding return order")
    picking_count = fields.Integer(compute="_compute_delivery",
                                   string='Picking Order', copy=False,
                                   default=0,
                                   store=True,
                                   help="Picking count")
    delivery_count = fields.Integer(compute="_compute_delivery",
                                    string='Delivery Order', copy=False,
                                    default=0,
                                    store=True,
                                    help="Delivery Count")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'), ('done', 'Done'),
                              ('cancel', 'Canceled')],
                             string='Status', readonly=True, default='draft',
                             help="State")
    source_pick_ids = fields.One2many('stock.picking',
                                      'return_order_id',
                                      string="Source Delivery",
                                      domain="[('return_order_pick_id',"
                                             "'=',False)]",
                                      help="Shows the delivery orders of the "
                                           "corresponding return order")
    note = fields.Text("Note", help="Note field")
    to_refund = fields.Boolean(string='Update SO/PO Quantity',
                               help='Trigger a decrease of the'
                                    ' delivered/received quantity in'
                                    ' the associated Sale '
                                    'Order/Purchase Order')

    def return_confirm(self):
        """Confirm the sale return"""
        if not self.source_pick_ids:
            stock_picks = self.env['stock.picking'].search([
                ('origin', '=', self.sale_order_id.name)])
            moves = (stock_picks.mapped('move_ids_without_package').filtered
                     (lambda p: p.product_id == self.product_id))
        else:
            moves = (self.source_pick_ids.mapped
                     ('move_ids_without_package').filtered
                     (lambda p: p.product_id == self.product_id))
        if moves:
            moves = moves.sorted('product_uom_qty', reverse=True)
            return_pick_wizard = (self.env['stock.return.picking'].create
                                  ({'picking_id': moves[0].picking_id.id}))
            return_pick_wizard._onchange_picking_id()
            return_pick_wizard.product_return_moves.unlink()
            lines = {'product_id': self.product_id.id,
                     "quantity": self.quantity,
                     'wizard_id': return_pick_wizard.id,
                     'move_id': moves[0].id, 'to_refund': self.to_refund}
            self.env['stock.return.picking.line'].create(lines)
            return_pick = return_pick_wizard._create_returns()
            if return_pick:
                return_pick = self.env['stock.picking'].browse(return_pick[0])
                return_pick.update({'note': self.reason})
                return_pick.write({'return_order_id': False,
                                   'return_order_pick_id': self.id,
                                   'return_order_picking': True})
                self.write({'state': 'confirm'})

    def return_cancel(self):
        """Cancel the return"""
        self.write({'state': 'cancel'})
        if self.source_pick_ids:
            for rec in (self.source_pick_ids.filtered(lambda s:
                                                      s.state not in
                                                      ['done', 'cancel'])):
                rec.action_cancel()

    def _get_report_base_filename(self):
        """Fetch report name"""
        self.ensure_one()
        return 'Sale Return - %s' % (self.name)

    def _compute_access_url(self):
        """URL accessing"""
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
                rec.delivery_count = self.env['stock.picking'].search_count(
                    [('return_order_id', 'in', self.ids),
                     ('return_order_picking', '=', False)])
            if rec.stock_picking_ids:
                rec.picking_count = len(rec.stock_picking_ids)
            else:
                rec.picking_count = self.env['stock.picking'].search_count(
                    [('return_order_pick_id', 'in', self.ids),
                     ('return_order_picking', '=', True)])

    def action_view_picking(self):
        """Function to view the stock picking transfers"""
        action = (self.env["ir.actions.actions"]._for_xml_id
                  ("stock.action_picking_tree_all"))
        pickings = self.mapped('stock_picking_ids')
        if not self.stock_picking_ids:
            pickings = self.env['stock.picking'].search(
                [('return_order_pick_id', '=', self.id),
                 ('return_order_picking', '=', True)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in
                                               action['views']
                                               if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = (pickings.filtered
                      (lambda x: x.picking_type_id.code == 'outgoing'))
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context,
                                 default_partner_id=self.partner_id.id,
                                 default_picking_type_id=
                                 picking_id.picking_type_id.id)
        return action

    def action_view_delivery(self):
        """Function to view the delivery transfers"""
        action = (self.env["ir.actions.actions"]._for_xml_id
                  ("stock.action_picking_tree_all"))
        pickings = self.mapped('stock_picking_ids')
        if not self.stock_picking_ids:
            pickings = self.env['stock.picking'].search(
                [('return_order_id', '=', self.id),
                 ('return_order_picking', '=', False)])
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in
                                               action['views']
                                               if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = (pickings.filtered(lambda x:
                                        x.picking_type_id.code == 'outgoing'))
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context,
                                 default_partner_id=self.partner_id.id,
                                 default_picking_type_id=
                                 picking_id.picking_type_id.id)
        return action

    @api.onchange('sale_order', 'source_pick')
    def onchange_sale_order(self):
        """All the fields are updated according to the sale order"""
        delivery = None
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id

            delivery = self.env['stock.picking'].search([
                ('origin', '=', self.sale_order_id.name)])
        if self.source_pick_ids:
            delivery = self.source_pick_ids
        if delivery:
            product_ids = (
                delivery.move_ids_without_package.mapped('product_id').ids)
            delivery = delivery.ids
        else:
            product_ids = self.sale_order_id.order_line.mapped('product_id').ids

        return {'domain': {'source_pick': [('id', 'in', delivery)],
                           'product_id': [('id', 'in', product_ids)]}}

    @api.onchange('product_id')
    def onchange_product_id(self):
        """Return Stock Valuation"""
        if self.product_id and self.source_pick_ids:
            moves = (self.source_pick_ids.mapped('move_ids_without_package').
                     filtered(lambda p: p.product_id == self.product_id))
            if moves:
                self.received_qty = sum(moves.mapped('quantity_done'))
