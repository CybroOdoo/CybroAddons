# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, models, fields
from odoo.exceptions import UserError, ValidationError


class MRPOrder(models.Model):
    """Creates the model named mrp.order"""
    _name = 'mrp.order'
    _description = "Manufacturing Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.model
    def _get_default_location_src_id(self):
        """Method _get_default_location_src_id to assign the value to the field
        location_src_id by default"""
        location = False
        company_id = self.env.context.get('default_company_id',
                                          self.env.company.id)
        if self.env.context.get('default_picking_type_id'):
            location = self.env['stock.picking.type'].browse(self.env.context[
                                                                 'default_picking_type_id']).default_location_src_id
        if not location:
            location = self.env['stock.warehouse'].search(
                [('company_id', '=', company_id)], limit=1).lot_stock_id
        return location and location.id or False

    location_src_id = fields.Many2one('stock.location',
                                      default=lambda self: self._get_default_location_src_id(),
                                      string='Default Location',
                                      help='Default source location of the '
                                           'mrp order')
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True, domain="""[
            ('is_storable', '=', True), '|', ('company_id', '=', False),
            ('company_id', '=', company_id)]""", help='Product to be created')
    name = fields.Char(
        string='Reference', copy=False, readonly=True,
        default=lambda self: self.env._('New'), help='Name of the MRP order')
    product_qty = fields.Float(string="Quantity To Manufacture", default=1.0,
                               tracking=True,
                               help='Quantity of the product to manufacture')
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user,
                              help='User responsible for the mrp order')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 index=True, required=True,
                                 help='Company corresponding to the order')
    uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure',
                             required=True,
                             help='Unit of Measurement of the product to '
                                  'manufacture')
    date_planned = fields.Datetime('Scheduled Date', copy=False,
                                   default=fields.Datetime.now,
                                   help="Date at which production start.",
                                   index=True, required=True)
    bom_id = fields.Many2one('simple.mrp.bom', string="Bills of Material",
                             help='Bill of Material of the product')
    line_ids = fields.One2many('mrp.order.line', 'mrp_id', string="Components",
                               help='Components needed to create the product')
    stock_line_ids = fields.One2many('stock.move', 'mrp_id', string='Products',
                                     help='Stock move lines of the mrp order')
    stock_move_id = fields.Many2one('stock.move', string='Stock Move',
                                    help='Stock move of the mrp order')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string='State',
        copy=False, index=True, readonly=True,
        store=True, tracking=True, default='draft',
        help='State of the mrp order')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """ Update the Uom for the product """
        self.uom_id = self.product_id.uom_id.id
        bom_id = self.env['simple.mrp.bom'].search([
            ('product_id', '=', self.product_id.id)
        ], limit=1)
        if self.product_id:
            self.bom_id = bom_id or False

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        """ Update the Uom for the product """
        multiple = 1.0
        if self.uom_id and self.bom_id.uom_id:
            multiple = self.uom_id._compute_quantity(1.0, self.bom_id.uom_id, raise_if_failure=False)
        self.stock_line_ids = False
        self.line_ids = False
        vals = []
        for rec in self.bom_id.line_ids:
            vals.append((0, 0, {
                'product_id': rec.product_id.id,
                'product_qty': rec.product_qty * self.product_qty * multiple,
                'uom_id': rec.uom_id.id,
            }))
        self.line_ids = vals
        destination = self.env.ref('simple_mrp_order.location_simple_mrp')
        location_src = self.location_src_id or self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id or self.env.company.id)], limit=1
        ).lot_stock_id
        if not self.location_src_id and location_src:
            self.location_src_id = location_src.id
        stock_vals = []
        for line in self.bom_id.line_ids:
            stock_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty * self.product_qty * multiple,
                'reference': line.product_id.name,
                'company_id': self.company_id.id,
                'location_id': location_src.id if location_src else False,
                'location_dest_id': destination.id,
                'uom_id': line.uom_id.id,
                'state': 'draft',
                'allowed_uom_ids': line.uom_id.relative_uom_id,
                'quantity': self.product_qty,
                'picked': True,
            }))
        self.stock_line_ids = stock_vals

    def _prepare_stock_line_vals(self, vals, company_id=None):
        """Ensure stock_line_ids have required reference, location_id, and location_dest_id."""
        stock_lines = vals.get('stock_line_ids')
        if not stock_lines:
            return
        company = (
            company_id
            or vals.get('company_id')
            or (self and self.company_id.id)
            or self.env.company.id
        )
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', company)], limit=1
        )
        location_id = (
            vals.get('location_src_id')
            or (self and self.location_src_id.id)
            or (warehouse.lot_stock_id.id if warehouse else False)
        )
        destination_id = self.env.ref('simple_mrp_order.location_simple_mrp').id

        for item in stock_lines:
            # item format: [command, id, values_dict]
            if isinstance(item, (list, tuple)) and len(item) >= 3 and isinstance(item[2], dict):
                product_id = item[2].get('product_id')
                if product_id and not item[2].get('reference'):
                    product = self.env['product.product'].browse(product_id)
                    item[2]['reference'] = product.name
                if not item[2].get('location_id'):
                    item[2]['location_id'] = location_id
                if not item[2].get('location_dest_id'):
                    item[2]['location_dest_id'] = destination_id
                if not item[2].get('company_id'):
                    item[2]['company_id'] = company

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add sequence and stock line defaults for MRP Orders."""
        for val in vals_list:
            self._prepare_stock_line_vals(val, company_id=val.get('company_id'))
            if not val.get('name') or val.get('name') == self.env._("New"):
                val['name'] = self.env['ir.sequence'].next_by_code('mrp.order') or self.env._("New")
        return super().create(vals_list)

    def write(self, vals):
        """Override write to ensure stock move lines have source and destination locations."""
        for rec in self:
            rec._prepare_stock_line_vals(vals, company_id=vals.get('company_id') or rec.company_id.id)
        return super().write(vals)

    @api.onchange('bom_id', 'product_qty')
    def _onchange_bom_id(self):
        """ Update the Components for the MRP Order """
        self.line_ids = False
        self.stock_line_ids = False
        self.product_id = self.bom_id.product_id.id
        vals = []
        for line in self.bom_id.line_ids:
            vals.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty * self.product_qty,
                'uom_id': line.uom_id.id,
            }))
        val = []
        destination = self.env.ref('simple_mrp_order.location_simple_mrp')
        location_src = self.location_src_id or self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id or self.env.company.id)], limit=1
        ).lot_stock_id
        if not self.location_src_id and location_src:
            self.location_src_id = location_src.id
        for line in self.bom_id.line_ids:
            val.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty * self.product_qty,
                'reference': line.product_id.name,
                'company_id': self.company_id.id,
                'location_id': location_src.id if location_src else False,
                'location_dest_id': destination.id,
                'uom_id': line.uom_id.id,
                'state': 'draft',
                'allowed_uom_ids': line.uom_id.relative_uom_id,
                'quantity': self.product_qty,
                'picked': True
            }))
        self.stock_line_ids = val
        self.line_ids = vals

    def action_confirm(self):
        """Method action_confirm to confirm the mrp order"""
        for order in self:
            for line in order.stock_line_ids:
                qty_needed = line.product_uom_qty or line.product_qty
                if qty_needed > line.product_id.qty_available:
                    raise ValidationError(self.env._(
                        'Only %(qty)s quantity available for %(product)s',
                        qty=line.product_id.qty_available,
                        product=line.product_id.name,
                    ))
            order.write({
                'state': 'confirmed',
            })

    def action_done(self):
        """Method action_done to make the mrp order done"""
        for order in self:
            if order.state != 'confirmed':
                raise UserError(self.env._('Only confirmed orders can be marked as done.'))
            order.write({
                'state': 'done'
            })
            for move in order.stock_line_ids:
                move._action_confirm()
                move._action_assign()
                move.move_line_ids.write({'quantity': move.product_uom_qty})
                move.picked = True
                move._action_done()
            source = self.env.ref('simple_mrp_order.location_simple_mrp')
            dest_location = order.location_src_id or self.env['stock.warehouse'].search(
                [('company_id', '=', order.company_id.id)], limit=1
            ).lot_stock_id
            move_id = self.env['stock.move'].create({
                'product_id': order.product_id.id,
                'product_uom_qty': order.product_qty,
                'reference': order.product_id.name,
                'company_id': order.company_id.id,
                'location_id': source.id,
                'location_dest_id': dest_location.id,
                'uom_id': order.uom_id.id,
                'state': 'draft',
                'allowed_uom_ids': order.uom_id.relative_uom_id,
                'origin': order.name,
                'quantity': order.product_qty,
                'picked': True
            })
            move_id._action_confirm()
            move_id._action_assign()
            move_id.move_line_ids.write({'quantity': move_id.product_uom_qty})
            move_id._action_done()
            order.stock_move_id = move_id

    def action_cancel(self):
        """Method action_cancel to cancel the mrp order"""
        self.write({
            'state': 'cancel'
        })

    def action_view_move(self):
        """Method action_view_move to view the stock moves from the smart
        button"""
        self.ensure_one()
        ids = [stock.id for stock in self.stock_line_ids]
        if self.stock_move_id:
            ids.append(self.stock_move_id.id)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'domain': [('id', 'in', ids)],
            'name': self.env._("Product Stock Move"),
            'target': 'current',
            'view_mode': 'list',
        }


class StockMove(models.Model):
    """Inherits the already existing model stock.move to add mrp_id field to the
    model for the working of this module"""
    _inherit = 'stock.move'

    mrp_id = fields.Many2one('mrp.order', string="MRP Order",
                             help="MRP Order related to the stock move")
