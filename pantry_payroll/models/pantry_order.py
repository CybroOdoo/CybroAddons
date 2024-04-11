# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
from odoo import api, fields, models


class PantryOrder(models.Model):
    """A class that represents a new model pantry order"""
    _name = 'pantry.order'
    _description = 'Pantry Order'
    _inherit = 'mail.thread'

    name = fields.Char(string='Order Sequence', readonly=True,
                       help='Sequence of the order')
    partner_id = fields.Many2one('res.partner', string='Order User',
                                 readonly=True,
                                 default=lambda self: self.env.user.partner_id,
                                 help='The user who is ordering')
    state = fields.Selection(string='Status', required=True, selection=[
        ('draft', 'Draft'), ('confirmed', 'Confirmed')], default='draft',
                             help='The current status of the order')
    date_order = fields.Datetime(string='Order Date',
                                 default=fields.Datetime.now, readonly=True,
                                 help='The date order')
    order_line_ids = fields.One2many('pantry.order.line',
                                     'pantry_order_id',
                                     string='Order Line', help="Order lines")
    amount_total = fields.Float(string='Total', compute='_compute_amount_total',
                                help='The total amount of the order')

    @api.model
    def create(self, vals):
        """Sequence for the order"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'pantry.order') or 'New'
        res = super(PantryOrder, self).create(vals)
        return res

    @api.depends('order_line_ids')
    def _compute_amount_total(self):
        """Calculates the amount_total"""
        for rec in self:
            rec.amount_total = sum(
                rec.mapped('order_line_ids').mapped('subtotal'))

    def action_confirm_pantry_order(self):
        """Change the state to confirmed"""
        self.state = 'confirmed'


class PantryOrderLine(models.Model):
    """A class that represents a new model pantry order line"""
    _name = 'pantry.order.line'
    _description = 'Pantry Order Line'

    pantry_order_id = fields.Many2one('pantry.order', string='Pantry Order',
                                      required=True,
                                      help='The corresponding pantry order')
    product_id = fields.Many2one('product.product', string='Product',
                                 required=True,
                                 domain=[('pantry_product', '=', True)],
                                 help='The product to order')
    quantity = fields.Float(string='Quantity',
                            help='The quantity of the product')
    unit_price = fields.Float(string='Unit Price',
                              help='The unit price of the product')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal',
                            help='The subtotal of the order line')

    @api.depends('quantity')
    def _compute_subtotal(self):
        """Calculates the subtotal"""
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price
