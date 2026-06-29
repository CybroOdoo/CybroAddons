# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#     Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#     Author: Anaswara S (odoo@cybrosys.com)
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
from datetime import datetime
from odoo import api, fields, models


class WashingWashing(models.Model):
    """Washing activity generating model"""
    _name = 'washing.washing'
    _description = 'Washing Washing'

    name = fields.Char(string='Work', help='Mention the work')
    laundry_works = fields.Boolean(default=False, help='For set conditions')
    user_id = fields.Many2one('res.users',
                              string='Assigned Person',
                              help="Name of assigned person")
    washing_date = fields.Datetime(string='Date', help="Date of washing")
    description = fields.Text(string='Description',
                              help='Add the description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, default='draft',
        help='State of wash')
    laundry_id = fields.Many2one('laundry.order.line')
    product_line_ids = fields.One2many('wash.order.line', 'wash_id',
                                       string='Products',
                                       help='Related Products for wash.')
    total_amount = fields.Float(compute='_compute_total_amount',
                                string='Grand Total')

    def start_wash(self):
        """Function for initiating the activity of washing."""
        if not self.laundry_works:
            self.laundry_id.state = 'wash'
            self.laundry_id.laundry_id.state = 'process'
        for wash in self:
            for line in wash.product_line_ids:
                self.env['sale.order.line'].create(
                    {'product_id': line.product_id.id,
                     'name': line.name,
                     'price_unit': line.price_unit,
                     'order_id': wash.laundry_id.laundry_id.sale_id.id,
                     'product_uom_qty': line.quantity,
                     'product_uom_id': line.uom_id.id,
                     })
        self.state = 'process'

    def action_set_to_done(self):
        """Function for set to done."""
        self.state = 'done'
        f = 0
        if not self.laundry_works:
            if self.laundry_id.extra_work_ids:
                for each in self.laundry_id.extra_work_ids:
                    self.create({'name': each.name,
                                 'user_id': each.assigned_person_id.id,
                                 'description': self.laundry_id.description,
                                 'laundry_id': self.laundry_id.id,
                                 'state': 'draft',
                                 'laundry_works': True,
                                 'washing_date': datetime.now().strftime(
                                     '%Y-%m-%d %H:%M:%S')})
                self.laundry_id.state = 'extra_work'
        laundry_id = self.search([('laundry_id.laundry_id', '=',
                                   self.laundry_id.laundry_id.id)])
        for each in laundry_id:
            if each.state != 'done' or each.state == 'cancel':
                f = 1
                break
        if f == 0:
            self.laundry_id.laundry_id.state = 'done'
        laundry = self.search([('laundry_id', '=', self.laundry_id.id)])
        f1 = 0
        for each in laundry:
            if each.state != 'done' or each.state == 'cancel':
                f1 = 1
                break
        if f1 == 0:
            self.laundry_id.state = 'done'

    @api.depends('product_line_ids')
    def _compute_total_amount(self):
        """Total of the line"""
        total = 0
        for obj in self:
            for each in obj.product_line_ids:
                total += each.subtotal
            obj.total_amount = total


class WashOrderLine(models.Model):
    """For creating order lines in washing."""
    _name = 'wash.order.line'
    _description = 'Wash Order Line'

    wash_id = fields.Many2one('washing.washing', string='Order Reference',
                              help='Order reference from washing',
                              ondelete='cascade')
    name = fields.Text(string='Description', required=True,
                       help='Add description')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure ', required=True)
    quantity = fields.Integer(string='Quantity',
                              help='Add the required quantity')
    product_id = fields.Many2one('product.product', string='Product',
                                 help='Order line Product')
    price_unit = fields.Float('Unit Price',
                              related='product_id.list_price',
                              help='Unit price of Product')
    subtotal = fields.Float(compute='_compute_subtotal', string='Subtotal',
                            readonly=True, store=True,
                            help='Subtotal of the order line')

    @api.depends('price_unit', 'quantity')
    def _compute_subtotal(self):
        """Computing the subtotal"""
        total = 0
        for wash in self:
            total += wash.price_unit * wash.quantity
        wash.subtotal = total
