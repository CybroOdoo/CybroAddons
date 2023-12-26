# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models
from odoo.addons.purchase_stock.models.purchase import PurchaseOrder


class PurchaseOrderLine(models.Model):
    """ Added picking type for each purchase order line """
    _inherit = 'purchase.order.line'

    picking_type_id = fields.Many2one('stock.picking.type',
                                      string='Deliver To',
                                      help="Mark the picking type",
                                      domain=[('code', '=', 'incoming')])
    picking_name = fields.Char(string='picking name',
                               help='For identifying picking type name')


class PurchaseOrder(PurchaseOrder):
    """ create multiple picking for the purchase order based on the deliver
                to given in the purchase order line"""
    _inherit = 'purchase.order'

    picking_count = fields.Integer(string='Picking Count',
                                   help="count of picking created for the"
                                        " purchase order")
    is_picked = fields.Boolean(string="Is picked",
                               compute="_compute_is_picked",
                               help="For managing whether product picking is "
                                    "done or not")

    def action_picking_view(self):
        """ The function will return tree view for the picking for the current
         purchase order"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfers',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'context': {'create': False},
            'domain': [
                ('is_multi', '=', True), ('origin', '=', self.name)],
        }

    def _create_picking(self):
        """ Over writing this function to create multiple picking based on the
            'deliver to' given in the purchase order line"""
        for order in self.order_line:
            picking_id = self.env['stock.picking'].search(
                [('is_multi', '=', True), ('origin', '=', self.name),
                 ('picking_type_id', '=', order.picking_type_id.id)])
            if order.picking_type_id and self.order_line.filtered(
                    lambda x: x.picking_type_id.id == order.picking_type_id.id
                              and x.id != order.id):
                if picking_id and order.picking_type_id == picking_id.picking_type_id:
                    picking_id.update({
                        'move_ids': [(fields.Command.create({
                            'product_id': order.product_id.id,
                            'product_uom_qty': order.product_qty,
                            'location_dest_id':
                                self._get_destination_location(),
                            'location_id':
                                self.partner_id.property_stock_supplier.id,
                            'description_picking': order.product_id.name,
                            'name': order.product_id.name,
                        }))]
                    })
                    if picking_id:
                        picking_id.action_confirm()
                else:
                    picking_id = self.create_picking(order)
                    picking_id.update({
                        'move_ids': [(fields.Command.create({
                            'product_id': order.product_id.id,
                            'product_uom_qty': order.product_qty,
                            'location_dest_id':
                                self._get_destination_location(),
                            'location_id':
                                self.partner_id.property_stock_supplier.id,
                            'description_picking': order.product_id.name,
                            'name': order.product_id.name,
                        }))]
                    })
                    if picking_id:
                        picking_id.action_confirm()
                order.picking_name = \
                    picking_id.picking_type_id.warehouse_id.name \
                    + ': ' + picking_id.picking_type_id.name
            elif order.picking_type_id:
                picking_id = self.env['stock.picking'].create({
                    'picking_type_id': order.picking_type_id.id,
                    'partner_id': order.order_id.partner_id.id,
                    'scheduled_date': fields.Datetime.today(),
                    'origin': order.order_id.name,
                    'picking_type_code': 'incoming',
                    'is_multi': True,
                    'company_id': order.picking_type_id.company_id.id,
                    'move_ids': [(fields.Command.create({
                        'product_id': order.product_id.id,
                        'product_uom_qty': order.product_qty,
                        'location_dest_id': self._get_destination_location(),
                        'location_id':
                            self.partner_id.property_stock_supplier.id,
                        'description_picking': order.product_id.name,
                        'name': order.product_id.name,
                    }))]
                })
                if picking_id:
                    picking_id.action_confirm()
                order.picking_name = \
                    picking_id.picking_type_id.warehouse_id.name \
                    + ': ' + picking_id.picking_type_id.name
                self.picking_count += 1
            elif not order.picking_type_id and self.order_line.filtered(
                    lambda x: x.picking_type_id.id == self.picking_type_id.id):
                picking_id = self.env['stock.picking'].search(
                    [('is_multi', '=', True), ('origin', '=', self.name),
                     ('picking_type_id', '=', self.picking_type_id.id)])
                if not picking_id:
                    picking_id = self.create_picking(order)
                picking_id.update({
                    'move_ids': [(fields.Command.create({
                        'product_id': order.product_id.id,
                        'product_uom_qty': order.product_qty,
                        'location_dest_id': self._get_destination_location(),
                        'location_id': self.partner_id.property_stock_supplier.id,
                        'description_picking': order.product_id.name,
                        'name': order.product_id.name,
                    }))]
                })
                # })
                if picking_id:
                    picking_id.action_confirm()
                    order.picking_name = \
                        picking_id.picking_type_id.warehouse_id.name \
                        + ': ' + picking_id.picking_type_id.name
            else:
                picking_id = self.env['stock.picking'].create({
                    'picking_type_id': self.picking_type_id.id,
                    'partner_id': order.order_id.partner_id.id,
                    'scheduled_date': fields.Datetime.today(),
                    'origin': order.order_id.name,
                    'location_id': self.partner_id.property_stock_supplier.id,
                    'location_dest_id': self._get_destination_location(),
                    'picking_type_code': 'incoming',
                    'is_multi': True,
                    'company_id': order.picking_type_id.company_id.id,
                    'move_ids': [(fields.Command.create({
                        'product_id': order.product_id.id,
                        'product_uom_qty': order.product_qty,
                        'location_dest_id': self._get_destination_location(),
                        'location_id': self.partner_id.property_stock_supplier.id,
                        'description_picking': order.product_id.name,
                        'name': order.product_id.name,
                    }))]
                })
                if picking_id:
                    picking_id.action_confirm()
                order.picking_name = \
                    picking_id.picking_type_id.warehouse_id.name \
                    + ': ' + picking_id.picking_type_id.name
                self.picking_count += 1
                return True

    def create_picking(self, order):
        """ Function to create picking only """
        if order.picking_type_id:
            picking_type_id = order.picking_type_id.id
        else:
            picking_type_id = self.picking_type_id.id
        picking_id = self.env['stock.picking'].create({
            'picking_type_id': picking_type_id,
            'partner_id': order.order_id.partner_id.id,
            'scheduled_date': fields.Datetime.today(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'location_dest_id': self._get_destination_location(),
            'origin': order.order_id.name,
            'picking_type_code': 'incoming',
            'is_multi': True,
            'company_id': order.picking_type_id.company_id.id,
        })
        self.picking_count += 1
        return picking_id

    def action_view_multi_picking(self):
        """ Function that to receive product"""
        result = self.env["ir.actions.actions"]._for_xml_id(
            'stock.action_picking_tree_all')
        result['context'] = {'default_partner_id': self.partner_id.id,
                             'default_origin': self.name,
                             'default_picking_type_id': self.picking_type_id.id}
        result['domain'] = [('is_multi', '=', True),
                            ('origin', '=', self.name)]
        return result

    def button_cancel(self):
        """ Cancel the pickings that are created through this module  when
                    purchase order cancel"""
        res = super(PurchaseOrder, self).button_cancel()
        pickings = self.env['stock.picking'].search([
            ('origin', '=', self.name)])
        for picking in pickings:
            picking.action_cancel()
        return res

    def _compute_is_picked(self):
        """ For computing whether the picking is completed or not"""
        picking_ids = self.env['stock.picking'].search(
            [('origin', '=', self.name)])
        if picking_ids:
            for picking in picking_ids:
                self.is_picked = True if picking.state == "done" else False
        else:
            self.is_picked = False
