# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ReturnOrder(models.Model):
    """Creating model for returning order"""
    _name = 'sale.return'
    _inherit = ['portal.mixin']
    _rec_name = "name"
    _order = "name"
    _description = "Sale Return"

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('sale.return')

    active = fields.Boolean(string='Active', default=True, help='Active')
    name = fields.Char(string="Name", default=_get_default_name,
                       help='Name of order')
    sale_order_id = fields.Many2one('sale.order', string="Sale Order",
                                 required=True, help='Correspondent sale order')
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help='Partner of return order')
    user_id = fields.Many2one('res.users', string="Responsible",
                              default=lambda self: self.env.user,
                              help="User of the order")
    create_date = fields.Datetime(string="Create Date",
                                  help="Create date of the order")
    stock_picking_ids = fields.One2many('stock.picking',
                                    'return_order_pick_id',
                                    domain="[('return_order_id','=',False)]",
                                    string="Return Picking",
                                    help="Shows the return picking of the"
                                         " corresponding return order")
    picking_count = fields.Integer(compute="_compute_delivery",
                                   string='Picking Order',
                                   copy=False, default=0, store=True,
                                   help="Number of pickings")
    delivery_count = fields.Integer(compute="_compute_delivery",
                                    string='Delivery Order', copy=False,
                                    default=0, store=True,
                                    help="Number of delivery")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('done', 'Done'), ('cancel', 'Canceled')],
                             string='Status', readonly=True, default='draft',
                             help="State of the return order")
    source_pick_ids = fields.One2many('stock.picking', 'return_order_id',
                                  string="Source Delivery",
                                  domain="[('return_order_pick_id','=',False)]",
                                  help="Shows the delivery orders of the"
                                       " corresponding return order")
    note = fields.Text("Note", help="Note to display")

    return_line_ids = fields.One2many('return.order.line',
                                      'order_id',
                                      string="Return Lines",
                                      help="Return order lines")

    def action_return_confirm(self):
        """Confirm the sale return"""
        if not self.source_pick_ids:
            stock_picks = self.env['stock.picking'].sudo().search([('origin', '=', self.sale_order_id.name)])
            moves = stock_picks.mapped('move_ids_without_package').sudo().filtered(
                lambda p: p.product_id.id in self.return_line_ids.mapped('product_id').ids)
        else:
            moves = self.source_pick_ids.mapped('move_ids_without_package').sudo().filtered(
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
                return_pick.write({'return_order_id': False, 'return_order_pick_id': self.id, 'return_order_picking': True})
                self.write({'state': 'confirm'})

    def action_return_cancel(self):
        """Cancel the return"""
        self.write({'state': 'cancel'})
        if self.stock_picking_ids:
            for rec in self.stock_picking_ids.sudo().filtered(lambda s: s.state not in ['done', 'cancel']):
                rec.action_cancel()

    def _get_report_base_filename(self):
        """seting the file name"""
        self.ensure_one()
        return 'Sale Return - %s' % (self.name)

    def _compute_access_url(self):
        """access url"""
        super(ReturnOrder, self)._compute_access_url()
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
                action['views'] = form_view + [(state, view) for state, view
                                        in action['views'] if view != 'form']
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
        action['context'] = dict(self._context,
                                 default_partner_id=self.partner_id.id,
                                 default_picking_type_id=picking_id.
                                 picking_type_id.id)
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
        action['context'] = dict(self._context,
                                 default_partner_id=self.partner_id.id,
                                 default_picking_type_id=picking_id.
                                 picking_type_id.id)
        return action

    @api.onchange('sale_order_id', 'source_pick_ids')
    def _onchange_sale_order_id(self):
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
    def _onchange_product_id(self):
        """Update the received quantity based on the selected product and source
         pick."""
        if self.product_id and self.source_pick_ids:
            moves = self.source_pick_ids.mapped(
                'move_ids_without_package').sudo().filtered(
                lambda p: p.product_id == self.product_id)
            if moves:
                self.received_qty = sum(moves.mapped('quantity_done'))
