# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class MRPOrder(models.Model):
    """Creates the model named mrp.order"""
    _name = 'mrp.order'
    _description = "Manufacturing Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.model
    def _get_default_location_src_id(self):
        """"Method _get_default_location_src_id to assign the value to the field
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
                                      default=_get_default_location_src_id,
                                      string='Default Location',
                                      help='Default source location of the '
                                           'mrp order')
    product_id = fields.Many2one('product.product', string="Product",
                                 required=True, domain="""[
            ('type', 'in', ['product', 'consu']),'|',('company_id', '=', False),
            ('company_id', '=', company_id)]""", help='Product to be created')
    name = fields.Char(
        string='Reference', copy=False, readonly=True,
        default=lambda x: _('New'), help='Name of the MRP order')
    product_qty = fields.Float(string="Quantity To Manufacture", default=1.0,
                               tracking=True,
                               help='Quantity of the product to manufacture')
    user_id = fields.Many2one('res.users', string='Responsible',
                              default=lambda self: self.env.user,
                              states={'done': [('readonly', True)]},
                              help='User responsible for the mrp order')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 index=True, required=True,
                                 help='Company corresponding to the order')
    uom_id = fields.Many2one('uom.uom', string='Product Unit of Measure',
                             required=True,
                             help='Unit of Measurement of the product to '
                                  'manufacture')
    uom_categ_id = fields.Many2one(related='product_id.uom_id.category_id')
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
    def onchange_product_id(self):
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
        multiple = 1
        if self.uom_id.uom_type == 'bigger':
            multiple = self.uom_id.factor_inv
        elif self.uom_id.uom_type == 'smaller':
            multiple = 1 / self.uom_id.factor
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
        for line in self.bom_id.line_ids:
            val = {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty * self.product_qty * multiple,
                'name': line.product_id.name,
                'company_id': self.company_id.id,
                'location_id': self.location_src_id.id,
                'location_dest_id': destination.id,
                'product_uom': line.uom_id.id,
                'state': 'draft',
                'product_uom_category_id': line.uom_id.category_id,
            }
            self.stock_line_ids = [fields.Command.create(val)]

    @api.model
    def create(self, vals):
        """Supering the already existing create method to add the sequence
        for the mrp order"""
        location_id = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1).lot_stock_id.id
        destination_id = self.env.ref('simple_mrp_order.location_simple_mrp').id
        if vals.get('stock_line_ids'):
            for item in vals.get('stock_line_ids'):
                product_name = self.env['product.product'].browse(
                    item[2].get('product_id')).name
                item[2]['location_id'] = location_id
                item[2]['location_dest_id'] = destination_id
                item[2]['name'] = product_name
        if "name" not in vals or vals["name"] == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "mrp.order"
            ) or _("New")
        return super().create(vals)

    @api.onchange('bom_id', 'product_qty')
    def onchange_bom_id(self):
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
        for line in self.bom_id.line_ids:
            val.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty * self.product_qty,
                'name': line.product_id.name,
                'company_id': self.company_id.id,
                'location_id': self.location_src_id.id,
                'location_dest_id': destination.id,
                'product_uom': line.uom_id.id,
                'state': 'draft',
                'product_uom_category_id': line.uom_id.category_id,
                'quantity': self.product_qty,
                'picked': True
            }))
        self.stock_line_ids = val
        self.line_ids = vals
        if self.bom_id:
            self.uom_id.category_id = self.uom_categ_id.id

    def action_confirm(self):
        """Method action_confirm to confirm the mrp order"""
        for line in self.stock_line_ids:
            if line.product_qty > line.product_id.qty_available :
                raise ValidationError('Only %s quantity available for %s' %
                                      (str(line.product_id.qty_available),
                                       str(line.product_id.name)))
        self.write({
            'state': 'confirmed',
        })

    def action_done(self):
        """Method action_done to make the mrp order done"""
        self.write({
            'state': 'done'
        })
        for move in self.stock_line_ids:
            move._action_confirm()
            move._action_assign()
            move.move_line_ids.write({'quantity': move.product_uom_qty})
            move.picked = True
            move._action_done()
        source = self.env.ref('simple_mrp_order.location_simple_mrp')
        move_id = self.env['stock.move'].create({
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_qty,
            'name': self.product_id.name,
            'company_id': self.company_id.id,
            'location_id': source.id,
            'location_dest_id': self.location_src_id.id,
            'product_uom': self.uom_id.id,
            'state': 'draft',
            'product_uom_category_id': self.uom_id.category_id,
            'origin': self.name,
            'quantity': self.product_qty,
            'picked': True
        })
        move_id._action_confirm()
        move_id._action_assign()
        move_id.move_line_ids.write({'quantity': move_id.product_uom_qty})
        move_id._action_done()
        self.stock_move_id = move_id

    def action_cancel(self):
        """Method action_cancel to cancel the mrp order"""
        self.write({
            'state': 'cancel'
        })

    def action_view_move(self):
        """Method action_view_move to view the stock moves from the smart
        button"""
        ids = [stock.id for stock in self.stock_line_ids]
        ids.append(self.stock_move_id.id)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'domain': [('id', 'in', ids)],
            'name': _("Product Stock Move"),
            'target': 'current',
            'view_mode': 'tree',
        }


class StockMove(models.Model):
    """Inherits the already existing model stock.move to add mrp_id field to the
    model for the working of this module"""
    _inherit = 'stock.move'

    mrp_id = fields.Many2one('mrp.order', string="MRP Order",
                             help="MRP Order related to the stock move")
